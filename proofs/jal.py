from nmigen import Const, Signal, ResetSignal, signed
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild

class ProofJal(ProofOverTicks): 
    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []


    def run_main_proof(self):
        m = self.module
        with m.If(self.time[1].at_instruction_start()):
            self.run_general()
            self.run_example()


    def run_example(self):
        """ Concrete example """
        m = self.module
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        with m.If(last.jtype.match(opcode=Opcode.Jal, rd=1, imm=-4)):
            comb += Assert(now.r.pc == (last.r.pc-4)[0:32])
            comb += Assert(now.r[1] == (last.r.pc+4)[0:32])
        with m.If(last.jtype.match(opcode=Opcode.Jal, imm=0)):
            comb += Assert(now.r.pc == (last.r.pc)[0:32])
        with m.If(last.jtype.match(opcode=Opcode.Jal, imm=4)):
            comb += Assert(now.r.pc == (last.r.pc+4)[0:32])
            

    def run_general(self):        
        last = self.time[1]
        now = self.time[0]
        m = self.module
        comb = m.d.comb

        with m.If(last.jtype.match(opcode=Opcode.Jal)):
            with m.If(last.jtype.rd == 0):
                now.assert_same_gpr(m, last.r)
            with m.Else():
                now.assert_same_gpr_but_one(m, last.r, last.jtype.rd)
                comb += Assert(now.r[last.jtype.rd] == (last.r.pc+4)[0:32])
            comb += Assert(now.r.pc == (last.r.pc+last.jtype.imm)[0:32])
            
    def simulate(self):
        return (MemBuild(0x200) 
            .j(0x100)

            .set_origin(0x300)
            .jal(imm=-16, rd=1) #300
            .nop() #304

            .set_origin(0x2F0)
            .addi(rs1=1,rd=2,imm=0) #x2=304
            .nop()
    ).dict