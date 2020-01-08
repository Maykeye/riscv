from nmigen import Const, Signal, ResetSignal, signed
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
                & last.at_instruction_start()
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

    def additional_check(self):
        return Const(1)

    def run_general(self):        
        """ General proof """
        m = self.module
        core : Core = self.uut
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        with m.If(self.additional_check() & last.at_instruction_start()):
            with m.If(last.itype.match(opcode=Opcode.OpImm, funct3=self.funct3())):
                with m.If(last.itype.rd == 0):
                    comb += Assert(now.r[0] == 0)
                    now.assert_same_gpr(m, last.r)
                with m.Else():
                    expected = Signal(core.xlen, name=f"{self.__class__.__name__}_expected")
                    actual =  Signal(core.xlen, name=f"{self.__class__.__name__}_got")
                    comb += actual.eq(now.r[last.itype.rd])
                    comb += expected.eq(self.general_proof_expr(last.r[last.itype.rs1], last.itype.imm))
                    comb += Assert(expected == actual)

                now.assert_pc_advanced(m, last.r)                
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



class ProofSLLI(ProofOppImm):
    def funct3(self):
        return OpImm.SHIFT_LEFT
    def examples(self):
                #RS1 RS1VAL RD   IMM     RESULT
        return [(3,  0b0101, 2,  3,     0b0101000),
                (3,  0b0101, 2,  0,     0b0101)]
    def general_proof_expr(self, last_rs1, last_imm):
        return (last_rs1 << last_imm[:5])[:32]



class ProofSRLI(ProofOppImm):
    def funct3(self):
        return OpImm.SHIFT_RIGHT
    def examples(self):
                #RS1 RS1VAL    RD   IMM     RESULT
        return [(3,  0b0101000, 2,  3,     0b0101),
                (3,  -1,        2,  2,     (1<<30)-1 )]
    def additional_check(self):
        return self.time[1].itype.imm[5:12] == 0
    def general_proof_expr(self, last_rs1, last_imm):
        result = (last_rs1 >> last_imm[:5])
        return result

class ProofSRAI(ProofOppImm):
    def funct3(self):
        return OpImm.SHIFT_RIGHT

    def additional_check(self):
        return self.time[1].itype.imm[10] == 1

    def examples(self):
                #RS1 RS1VAL     RD   IMM               RESULT
        return [(3,  0b0101000, 2,  3 | (1 << 10),     0b0101),
                (3,  -1,        2,  2 | (1 << 10),     -1 )]
    def general_proof_expr(self, last_rs1, last_imm):
        m = self.module
        core = self.uut
        signed_rs1 = Signal(signed(core.xlen), name="proof_srai_signed")
        m.d.comb += signed_rs1.eq(last_rs1)
        return (signed_rs1 >> last_imm[:5])[:32]

