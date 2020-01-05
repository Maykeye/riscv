from nmigen import Const, Signal, ResetSignal
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List

class ProofAndI(ProofOverTicks): 
    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []

    def run_main_proof(self):        
        self.run_general()
        self.run_example()


    def run_example(self):
        """ Concrete example """
        m = self.module
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]
        
        with m.If(Const(1)
            & last.input_ready 
            & last.itype.match(opcode=Opcode.OpImm, funct3=OpImm.AND, rs1=3, rd=2, imm=0b1011) 
            & (last.r[3] == 0b0101)
        ):            
            comb += Assert(now.r[2] == 1)


        with m.If(Const(1)
            & last.input_ready 
            & last.itype.match(opcode=Opcode.OpImm, funct3=OpImm.AND, rs1=1, imm=-1)             
        ):            
            comb += Assert(now.r[1] == last.r[1])


    def run_general(self):        
        """ General proof """
        m = self.module
        core : Core = self.uut
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        with m.If(last.itype.match(opcode=Opcode.OpImm, funct3=OpImm.AND) & last.input_ready):
            with m.If(last.itype.rd == 0):
                comb += Assert(now.r[0] == 0)
            with m.Else():
                addi_expecetd = Signal(core.xlen)
                comb += addi_expecetd.eq(last.r[last.itype.rs1] & last.itype.imm)
                comb += Assert(addi_expecetd == now.r[last.itype.rd])

            now.assert_pc_advanced(m, last)                
            now.assert_same_gpr_but_one(m, last.r, last.itype.rd)