from nmigen import Const, Signal, ResetSignal
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List

class ProofOppImm(ProofOverTicks): 
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

        for (rs1, rs1_val, rd, imm, result) in self.examples():
            rs1_value_matcher = (last.r[rs1] == rs1_val) if rs1_val is not None else Const(1)

            with m.If(Const(1)
                & last.input_ready 
                & last.itype.match(opcode=Opcode.OpImm, funct3=self.funct3(), rs1=rs1, rd=rd, imm=imm) 
                & rs1_value_matcher
            ):

                comb += Assert(now.r[rd] == result)

    def examples(self): #[(rs1, rs1_val, rd, imm, value)]
        raise Exception("Must be overwritten")
    
    def funct3(self):
        raise Exception("Must be overwritten")

    def general_proof_expr(self, last_rs1_val, last_imm):
        raise Exception("Must be overwritten")

    def run_general(self):        
        """ General proof """
        m = self.module
        core : Core = self.uut
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        with m.If(last.itype.match(opcode=Opcode.OpImm, funct3=self.funct3()) & last.input_ready):
            with m.If(last.itype.rd == 0):
                comb += Assert(now.r[0] == 0)
            with m.Else():
                expecetd = Signal(core.xlen, name=f"{self.__class__.__name__}_expected")
                comb += expecetd.eq(self.general_proof_expr(last.r[last.itype.rs1], last.itype.imm))
                comb += Assert(expecetd == now.r[last.itype.rd])

            now.assert_pc_advanced(m, last)                
            now.assert_same_gpr_but_one(m, last.r, last.itype.rd)

class ProofAddI(ProofOppImm):
    def examples(self):
                #RS1 RS1VAL RD  IMM RESULT
        return [(3,  5,      2,  10, 15),
                (3,  5,      3,  0b111111111111, 4)]
    def funct3(self):
        return OpImm.ADD
    def general_proof_expr(self, last_rs1, last_imm):
        return last_rs1 + last_imm


class ProofOrI(ProofOppImm):
    def examples(self):
                #RS1 RS1VAL RD   IMM     RESULT
        return [(3,  0b101,  2,  0b1011, 0b1111),
                (3,  None,   2,  -1,     -1)]
    def funct3(self):
        return OpImm.OR
    def general_proof_expr(self, last_rs1, last_imm):
        return last_rs1 | last_imm

class ProofAndI(ProofOppImm):
    def examples(self):
                #RS1 RS1VAL RD   IMM     RESULT
        return [(3,  0b101,  2,  0b1011, 1),
                (3,  None,   2,  -1,     self.time[1].r[3])]
    def funct3(self):
        return OpImm.AND
    def general_proof_expr(self, last_rs1, last_imm):
        return last_rs1 & last_imm


class ProofXorI(ProofOppImm):
    def examples(self):
                #RS1 RS1VAL RD   IMM     RESULT
        return [(3,  0b0101, 2,  0b1011, 0b1110),
                (3,  None,   3,  -1,     ~self.time[1].r[3])]
    def funct3(self):
        return OpImm.XOR
    def general_proof_expr(self, last_rs1, last_imm):
        return last_rs1 ^ last_imm