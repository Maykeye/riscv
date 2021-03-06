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
from register_file import RegisterFile, RegisterFileModule
from encoding import IType, UType, JType, BType
from clock_info import ClockInfo
from alu import ALU
from shifter import Shifter
from membus import MemoryBus

class Core(ElaboratableAbstract):
    def __init__(self, clock, look_ahead=1, addr_length=32, xlen=32, include_enable=False, include_debug_opcode=1):
        assert addr_length % 8 == 0, "address length must be octet aligned"
        assert xlen % 8 == 0, "register width must be octet aligned"

        assert look_ahead >= 1, "Core should see at least one full word ahead"
        self.look_ahead = look_ahead
        super().__init__()
        self.clock = clock

        # register width
        self.xlen = xlen
        # addr_length holds width of address bus
        self.addr_length = addr_length

        # add mem2core bus for reads
        self.mem2core = mem2core = MemoryBus(addr_length, xlen, "mem2core")
        self.add_existing_output_signal(mem2core.addr)
        self.add_existing_output_signal(mem2core.en)
        self.add_existing_output_signal(mem2core.seq)
        self.add_existing_input_signal(mem2core.ready)
        self.add_existing_input_signal(mem2core.value)

        # add core2mem bus for writes
        self.core2mem = core2mem = MemoryBus(addr_length, xlen, "core2mem")
        self.add_existing_output_signal(core2mem.addr)
        self.add_existing_output_signal(core2mem.en)
        self.add_existing_output_signal(core2mem.seq)
        self.add_existing_output_signal(core2mem.value)
        self.add_existing_input_signal(mem2core.ready)        

        # instruction implementation contains actual implementation of instructions
        self.instructions : List[Instruction] = []                

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
        self.btype = BType("btype")

        self.in_reset = Signal(reset=1)
        
        self.last_instruction = Signal(32)
        self.last_instruction_valid = Signal() #if true, continue execution from last_instruction, otherwise from input[0]
        self.current_instruction_valid = Signal()
        self.have_valid_instruction = Signal()
        self.current_instruction = Signal(32)

        self.cycle = Signal(4)
        self.next_pc = Signal(xlen)
        self.advance_pc = Signal()

        self.alu =  ALU(self.xlen, "alu")
        self.left_shifter = Shifter(xlen, Shifter.LEFT, "SL")
        self.right_shifter = Shifter(xlen, Shifter.RIGHT, "SR")
        self.register_file = RegisterFileModule(xlen)        
        
        self.pc = Signal(xlen, name="pc") #TODO: remove from register file? use additional signals in regfile?
        



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
        m.submodules.regs = self.register_file
        self.iclk = m.d.i

        m.d.comb += self.last_instruction_valid.eq(self.cycle != 0)
        

        with m.If((self.cycle == 0) & (self.mem2core.ready)):
            m.d.comb += self.current_instruction.eq(self.mem2core.value)
            m.d.comb += self.current_instruction_valid.eq(1)
        with m.Else():
            m.d.comb += self.current_instruction.eq(self.last_instruction)
            m.d.comb += self.current_instruction_valid.eq(0)

        m.d.comb += self.have_valid_instruction.eq(self.current_instruction_valid | self.last_instruction_valid)

        self.itype.elaborate(m.d.comb, self.current_instruction)
        self.utype.elaborate(m.d.comb, self.current_instruction)
        self.btype.elaborate(m.d.comb, self.current_instruction)
        self.jtype.elaborate(m.d.comb, self.current_instruction)
        
        m.d.comb += self.alu.en.eq(0)
        m.d.comb += self.advance_pc.eq(0)
        m.d.comb += self.next_pc.eq(0)
        

        if self.is_enabled is None:
            self.elaborate_impl(p)
        else:
            with m.If(self.is_enabled):
                self.elaborate_impl(p)

        self.advance_pc_if_needed()
        self.iclk += self.last_instruction.eq(self.current_instruction)
        return m

    def query_rs1(self, idx=None):
        """ Query register file throught RS1 port. If no index provided, rs1 from the current instruction is used """
        if idx is None:
            idx = self.itype.rs1
        comb = self.current_module.d.comb
        comb += self.register_file.rs1_in.eq(idx)
        return self.register_file.rs1_out

    def query_rs2(self, idx=None):
        """ Query register file throught RS2 port. If no index provided, rs2 from the current instruction is used """
        if idx is None:
            idx = self.btype.rs2
        comb = self.current_module.d.comb
        comb += self.register_file.rs2_in.eq(idx)
        return self.register_file.rs2_out

    def elaborate_impl(self, p:Platform) -> Module:
        m = self.current_module
        #comb = m.d.comb
        iclk = self.iclk
        self.emit_debug_opcode(DebugOpcode.NOT_SPECIFIED, 0)

        with m.If(self.in_reset):
            iclk += self.in_reset.eq(0)
            iclk += self.pc.eq(0x200)  
            self.mem2core.init_read(iclk, 0x200, 1)
            self.emit_debug_opcode(DebugOpcode.IN_RESET)     
        with m.Elif(self.have_valid_instruction):
            # Run instruction if data is ready
            first = True            
            for instr in self.instructions:
                if_inst = m.If if first else m.Elif
                with if_inst(instr.check()):
                    instr.implement()
                first = False
            with m.Else():
                self.emit_debug_opcode(DebugOpcode.INVALID)
                self.move_pc_to_next_instr()
                #TODO: add reg instruction_executed and check it instead?
        with m.Else():
            self.mem2core.init_read(self.iclk, self.pc, 1)
            self.emit_debug_opcode(DebugOpcode.AWAIT_READ)
 
        return m

    def call_alu(self, func : OpAlu, lhs : Statement, rhs : Statement): 
        """ Call ALU and return its output wire """
        comb = self.current_module.d.comb 

        comb += self.alu.lhs.eq(lhs)
        comb += self.alu.rhs.eq(rhs)        
        comb += self.alu.op.eq(func)        
        comb += self.alu.en.eq(1)

        return self.alu.output

        
    def call_left_shift(self, rs: Value, shamt : Statement):
        """ Call SHIFT-LEFT module and return its output wire """
        comb = self.current_module.d.comb         
        comb += self.left_shifter.input.eq(rs)
        comb += self.left_shifter.shamt.eq(shamt)
        return self.left_shifter.output

    def call_right_shift(self, rs: Value, shamt : Statement, msb : Statement):
        """ Call SHIFT-RIGHT module and return its output wire """
        comb = self.current_module.d.comb 
        comb += self.right_shifter.input.eq(rs)
        comb += self.right_shifter.msb.eq(msb)
        comb += self.right_shifter.shamt.eq(shamt)
        return self.right_shifter.output


    def emit_debug_opcode(self, op:DebugOpcode, x : Optional[Value] = None):
        if self.debug_opcode is not None:
            domain = self.current_module.d.comb
            domain += self.debug_opcode.eq(op)
            if x is not None:
                domain += self.debug_value.eq(x)

    def assign_pc(self, new_pc_value):
        self.current_module.d.comb += self.next_pc.eq(new_pc_value)
        self.current_module.d.comb += self.advance_pc.eq(1)        

    def move_pc_to_next_instr(self):
        """ Move PC to the start of the next instruction """
        self.assign_pc(self.pc + 4)

    def assign_gpr(self, idx:Value, value:Value):
        # R0 will be reassigned to 0 at the end of elaborate()
        comb = self.current_module.d.comb
        comb += self.register_file.rd.eq(idx)
        comb += self.register_file.rd_value.eq(value)
        

    def advance_pc_if_needed(self):
        m = self.current_module
        with m.If(self.advance_pc):
            self.iclk += self.pc.eq(self.next_pc)
            self.schedule_read(self.next_pc, 1)
            self.iclk += self.cycle.eq(0)            

    def schedule_read(self, addr, seq):
        self.mem2core.init_read(self.iclk, addr, seq)

    def make_fakemem(self, m : Module, mem : Dict[int, int]):
        comb : List[Statement] = m.d.comb
        with m.If(self.mem2core.en):
            with m.Switch(self.mem2core.addr):
                for address, value in mem.items():
                    with m.Case(address):
                        word_value = value | (mem.get(address+1, 0xff) << 8) | (mem.get(address+2, 0xff) << 16) | (mem.get(address+3, 0xff) << 24)
                        comb += self.mem2core.value.eq(word_value)
                with m.Default():
                    comb += self.mem2core.value.eq(0xFFFFFFFF) 
            comb += self.mem2core.ready.eq(1)
        with m.Else():
            comb += self.mem2core.ready.eq(1)
                

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
        
        
