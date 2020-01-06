import os
import re
import sys
from typing import List, Dict, Optional
import importlib

from nmigen import Elaboratable, Module, Signal, signed, unsigned, Cat, ClockDomain, ClockSignal, Const, Array, ResetSignal, Value
from nmigen.hdl.ast import Statement
from nmigen.asserts import Assert, Assume, Past, Cover
from nmigen.back.pysim import Simulator, Delay
from nmigen.build import Platform
from nmigen.cli import main_parser, main_runner
from enum import IntEnum
from skeleton import ElaboratableAbstract, fix_gtkw_win, dump_inputs, SeqPast
from skeleton import muS

from instruction import Instruction
from opcodes import DebugOpcode, OpAlu
from register_file import RegisterFile
from encoding import IType, UType, JType
from clock_info import ClockInfo
from alu import ALU
from shifter import Shifter


class Core(ElaboratableAbstract):
    def __init__(self, clock, look_ahead=1, addr_length=32, xlen=32, include_enable=False, include_debug_opcode=1):
        assert addr_length % 8 == 0, "address length must be octet aligned"
        assert xlen % 8 == 0, "register width must be octet aligned"

        assert look_ahead >= 1, "Core should see at least one full word ahead"
        super().__init__()
        self.clock = clock
        
        # Input Data holds N words that recently were read from memory
        # and meant to be executed by the CPU
        self.input_data = Array([self.add_input_signal(32, name=f"input_{i}") for i in range(look_ahead)])

        # register width
        self.xlen = xlen

        # input_ready shows which input was actually fetched from cpu
        self.input_ready = self.add_input_signal(look_ahead, name="input_ready")

        # addr_length holds width of address bus
        self.addr_length = addr_length
        
        # mem2core_addr is an address from which memory must be read
        self.mem2core_addr = self.add_output_signal(self.addr_length, name="mem2core_addr")

        # mem2core_re, mem2core read enable shows that core wants to read data from memory
        self.mem2core_en = self.add_output_signal(name="mem2core_re")
        
        # mem2core_seq indicates that core is going to read data in sequence.
        # core thinks that next read will be either from next byte or from next word
        self.mem2core_seq = self.add_output_signal(name="mem2core_seq")        

        # instruction implementation contains actual implementation of instructions
        self.instructions : List[Instruction] = []        
        self.r = RegisterFile(self.xlen)

        # is enabled is an optional input pin that can pauses RISCV
        self.is_enabled = Signal(name="en") if include_enable else None
        # debug opcode is an optional output signal which shows what instruction was executed on last cycle
        self.debug_opcode = self.add_output_signal(DebugOpcode, name="dbg_op") if include_debug_opcode else None
        self.debug_value = self.add_output_signal(xlen, name="dbg_val") if include_debug_opcode else None
        
        self.iclk = None
        self.current_module : Module = None

        self.itype = IType("itype")
        self.utype = UType("utype")
        self.jtype = JType("jtype")

        self.in_reset = Signal(reset=1)
        self.cycle = Signal(4)
        self.next_pc = Signal(xlen)
        self.advance_pc = Signal()

        self.alu =  ALU(self.xlen, "alu")
        self.left_shifter = Shifter(xlen, Shifter.LEFT, "SL")
        self.right_shifter = Shifter(xlen, Shifter.RIGHT, "SR")



    def add_instruction(self, implementation):
        self.instructions.append(implementation)
        implementation.core = self
        return implementation



    def elaborate(self, p:Platform) -> Module:
        m = Module()
        self.current_module = m
        m.submodules.alu = self.alu
        m.submodules.shl = self.left_shifter
        m.submodules.shr = self.right_shifter
        self.iclk = m.d.i
        self.itype.elaborate(m.d.comb, self.input_data[0])
        self.utype.elaborate(m.d.comb, self.input_data[0])
        self.jtype.elaborate(m.d.comb, self.input_data[0])
        
        m.d.comb += self.alu.en.eq(0)
        m.d.comb += self.advance_pc.eq(0)
        m.d.comb += self.next_pc.eq(0)
        

        if self.is_enabled is None:
            self.elaborate_impl(p)
        else:
            with m.If(self.is_enabled):
                self.elaborate_impl(p)

        self.iclk += self.r[0].eq(0)
        self.advance_pc_if_needed()
        return m


    def elaborate_impl(self, p:Platform) -> Module:
        m = self.current_module
        iclk = self.iclk
        self.emit_debug_opcode(DebugOpcode.NOT_SPECIFIED, 0)

        with m.If(self.in_reset):
            iclk += self.in_reset.eq(0)
            iclk += self.r.pc.eq(0x200)            
            iclk += self.mem2core_en.eq(1)
            iclk += self.mem2core_addr.eq(0x200)
            iclk += self.mem2core_seq.eq(1)
            self.emit_debug_opcode(DebugOpcode.IN_RESET)     
        with m.Elif(self.input_ready[0]):
            # Run instruction if data is ready
            first = True
            with m.If(self.input_ready[0]):
                for instr in self.instructions:
                    if first:
                        with m.If(instr.check()):
                            instr.implement()
                        first = False
                    else:
                        with m.Elif(instr.check()):
                            instr.implement()
                with m.Else():
                    self.emit_debug_opcode(DebugOpcode.INVALID)
                    self.move_pc_to_next_instr()
        with m.Else():
            iclk += self.mem2core_seq.eq(1)
            iclk += self.mem2core_en.eq(1)
            iclk += self.mem2core_addr.eq(self.r.pc)
            self.emit_debug_opcode(DebugOpcode.AWAIT_READ)
 
        return m

    def call_alu(self, rdst : Signal, func : OpAlu, lhs : Statement, rhs : Statement): 
        """ Call ALU and assign result to RDST on the next cycle """
        comb = self.current_module.d.comb 
        iclk = self.iclk
        # TODO: check for (rdst is r0)?

        comb += self.alu.lhs.eq(lhs)
        comb += self.alu.rhs.eq(rhs)        
        comb += self.alu.op.eq(func)        
        comb += self.alu.en.eq(1)

        iclk += rdst.eq(self.alu.output)

        
    def call_left_shift(self, rdst : Signal, rs: Value, shamt : Statement):
        comb = self.current_module.d.comb 
        iclk = self.iclk
        comb += self.left_shifter.input.eq(rs)
        comb += self.left_shifter.shamt.eq(shamt)
        iclk += rdst.eq(self.left_shifter.output)

    def call_right_shift(self, rdst : Signal, rs: Value, shamt : Statement, msb : Statement):
        comb = self.current_module.d.comb 
        iclk = self.iclk
        comb += self.right_shifter.input.eq(rs)
        comb += self.right_shifter.msb.eq(msb)
        comb += self.right_shifter.shamt.eq(shamt)
        iclk += rdst.eq(self.right_shifter.output)


    def emit_debug_opcode(self, op:DebugOpcode, x : Optional[Value] = None):
        if self.debug_opcode is not None:
            domain = self.current_module.d.comb
            domain += self.debug_opcode.eq(op)
            if x is not None:
                domain += self.debug_value.eq(x)

    def move_pc_to_next_instr(self, advance_by=4):
        """ Schedule pc to pc+advance_by """
        self.current_module.d.comb += self.next_pc.eq(self.r.pc + advance_by)
        self.current_module.d.comb += self.advance_pc.eq(1)

    def assign_gpr(self, idx:Value, value:Value):
        # R0 will be reassigned to 0 at the end of elaborate()
        self.iclk += self.r[idx].eq(value)

    def advance_pc_if_needed(self):
        m = self.current_module
        with m.If(self.advance_pc):
            self.iclk += self.r.pc.eq(self.next_pc)
            self.iclk += self.mem2core_seq.eq(1)
            self.iclk += self.mem2core_en.eq(1)
            self.iclk += self.mem2core_addr.eq(self.next_pc)


    def make_fakemem(self, m : Module, mem : Dict[int, int]):
        comb : List[Statement] = m.d.comb
        with m.If(self.mem2core_en):
            with m.Switch(self.mem2core_addr):
                for address, value in mem.items():
                    with m.Case(address):
                        word_value = value | (mem.get(address+1, 0xff) << 8) | (mem.get(address+2, 0xff) << 16) | (mem.get(address+3, 0xff) << 24)
                        comb += self.input_data[0].eq(word_value)
                with m.Default():
                    comb += self.input_data[0].eq(0xFFFFFFFF) 
            comb += self.input_ready.eq(1)
        with m.Else():
            comb += self.input_ready.eq(0)
                

    def simulate(self, top : Module, clk : ClockInfo, mem : Dict[int, int], n=30, filename_prefix="waves/test"):
        rst = clk.rst
        self.make_fakemem(top, mem)
        dump_inputs(self, top)

        def timings():            
            yield rst.eq(1)
            yield
            yield rst.eq(0)
            for _ in range(n):
                yield

        sim = Simulator(top)
        sim.add_clock(muS, domain="i")
        sim.add_sync_process(timings, domain="i")
        with sim.write_vcd(f"{filename_prefix}.vcd", f"{filename_prefix}.gtkw",  traces = self.ports()):
            sim.run()
        
        
