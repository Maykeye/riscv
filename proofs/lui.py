from nmigen import Const, Signal, ResetSignal, signed
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild

class ProofLui(ProofOverTicks): 
    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []


    def run_main_proof(self):
        m = self.module
        with m.If(self.time[1].input_ready & (self.time[1].utype.opcode == Opcode.Lui)):
            self.run_general()
            self.run_example()


    def run_example(self):
        """ Concrete example """
        m = self.module
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]


        with m.If(last.utype.match(rd=1, imm=0x80000)
                & last.r[1] == 1
        ):
            comb += Assert(now.r[1] == 0x80000)

        with m.If(last.utype.match(rd=1, imm=0xFFFFF000)):
            comb += Assert(now.r[1] == 0xFFFFF000)

        with m.If(last.utype.match(rd=1, imm=0xFF1FF000)):
            comb += Assert(now.r[1] == 0xFF1FF000)


    def run_general(self):        
        last = self.time[1]
        now = self.time[0]
        m = self.module
        comb = m.d.comb

        with m.If(last.utype.match(opcode=Opcode.Lui)):
            with m.If(last.jtype.rd == 0):
                now.assert_same_gpr(m, last.r)
            with m.Else():
                now.assert_same_gpr_but_one(m, last.r, last.utype.rd)
                comb += Assert(now.r[last.utype.rd] == last.utype.imm)
                comb += Assert(now.r[last.utype.rd][0:12] == 0)
            now.assert_pc_advanced(m, last)
            

    def simulate(self):
        return (MemBuild(0x200) 
            .lui(1, 0xFFFFF000)
            .lui(2, 0x00001000)
            .lui(3, 0x12345000)
            .dict
        )
