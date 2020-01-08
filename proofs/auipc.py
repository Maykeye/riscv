from nmigen import Const, Signal, ResetSignal, signed
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild

class ProofAuipc(ProofOverTicks): 
    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []


    def run_main_proof(self):
        m = self.module
        with m.If(self.time[1].input_ready & (self.time[1].utype.opcode == Opcode.Auipc)):
            self.run_general()
            self.run_example()


    def run_example(self):
        """ Concrete example """
        m = self.module
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        with m.If(last.utype.match(rd=1, imm=0)):
            comb += Assert(now.r[1] == last.r.pc)

        with m.If((last.utype.match(rd=1, imm=0x1234_5000)) & (last.r.pc == 0x200)):
            comb += Assert(now.r[1] == 0x1234_5200)

        with m.If((last.utype.match(rd=1, imm=0xF234_5000)) & (last.r.pc == 0x200)):
            comb += Assert(now.r[1] == 0xF234_5200)


    def run_general(self):
        """ General proof """
        last = self.time[1]
        now = self.time[0]
        m = self.module
        comb = m.d.comb
        
        with m.If(last.utype.rd == 0):
            now.assert_same_gpr(m, last.r)
        with m.Else():
            now.assert_same_gpr_but_one(m, last.r, last.utype.rd)
            comb += Assert(now.r[last.utype.rd] == (last.r.pc + last.utype.imm)[0:32])

        now.assert_pc_advanced(m, last.r)
            

    def simulate(self):
        return (MemBuild(0x200) 
            .auipc(1, 0x1000) # R1 = 1200
            .auipc(2, 0x1000) # R1 = 1204
            .auipc(3, 0x1000) # R1 = 1208
            .auipc(4, 0x1000) # R1 = 120B
            .nop()
            .nop()
            .nop()
            .nop()
            .dict
        )
