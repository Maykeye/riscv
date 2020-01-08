from nmigen import Const, Signal, ResetSignal, signed, Cat
from nmigen.asserts import Assert
from opcodes import Opcode, OpImm
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild

class ProofJalr(ProofOverTicks): 
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

        with m.If(last.itype.match(opcode=Opcode.Jalr, rd=1, imm=0x23, rs1=2, funct3=0)
            & (last.r[2] == 0x100)
        ):
            comb += Assert(now.r.pc == 0x122)

            

    def run_general(self):        
        last = self.time[1]
        now = self.time[0]
        m = self.module
        comb = m.d.comb
        core : Core = self.uut


        with m.If(last.itype.match(opcode=Opcode.Jalr) & (last.itype.funct3 == 0)):
            with m.If(last.itype.rd == 0):
                now.assert_same_gpr(m, last.r)
            with m.Else():
                now.assert_same_gpr_but_one(m, last.r, last.itype.rd)
                comb += Assert(now.r[last.itype.rd] == (last.r.pc+4)[0:32])
            
            sum = Signal(core.xlen)
            expected_jalr_pc = Signal(core.xlen)

            comb += sum.eq(last.r[last.itype.rs1] + last.itype.imm)
            comb += expected_jalr_pc.eq(Cat(Const(0,1), sum[1:core.xlen]))

            comb += Assert(now.r.pc == expected_jalr_pc)


    def simulate(self):
        return (MemBuild(0x200) 
            .addi(1,0,0x80)
            .jalr(2,1,0x200)

            .set_origin(0x280)
            .nop()            
            .nop()
            .nop()
        ).dict

