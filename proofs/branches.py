from nmigen import Const, Signal, ResetSignal, signed, unsigned
from nmigen.asserts import Assert
from opcodes import Opcode, OpBranch
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild
# TODO: example proofs


class ProofBranchBase(ProofOverTicks):
    def op_branch(self) -> OpBranch: 
        raise Exception("Not implemented in the child class")
    def run_general(self): 
        raise Exception("Not implemented in the child class")

    def run_main_proof(self):
        m = self.module
        with m.If(self.time[1].at_instruction_start() & self.time[1].btype.match(opcode=Opcode.Branch, funct3=self.op_branch())):
            self.run_general()
            self.run_example()
            self.time[0].assert_same_gpr(
                self.module, self.time[1].r, src_loc_at=2)

    def run_example(self):
        pass

    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut: Core, expect: bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []

    def assert_jump_was_taken(self):
        last = self.time[1]
        self.time[0].r.pc.eq((last.r.pc + last.btype.imm)[0:32])

    def assert_no_jump_taken(self):
        self.time[0].assert_pc_advanced(self.module, self.time[1].r, src_loc_at=2)


class ProofBEQ(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BEQ

    def run_general(self):
        last = self.time[1]
        m = self.module
        with m.If(last.r[last.btype.rs1] == last.r[last.btype.rs2]):
            self.assert_jump_was_taken()
        with m.Else():
            self.assert_no_jump_taken()

    def simulate(self):
        return (MemBuild(0x200)
                .addi(10, 0, 1)
                .addi(11, 0, 1)
                .beq(11, 0, 0x100)
                .beq(11, 10, 0x100)
                .set_origin(0x30c)
                .nop()
        ).dict


class ProofBNE(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BNE

    def run_general(self):
        last = self.time[1]
        m = self.module
        with m.If(last.r[last.btype.rs1] == last.r[last.btype.rs2]):
            self.assert_no_jump_taken()
        with m.Else():
            self.assert_jump_was_taken()

    def simulate(self):
        return (MemBuild(0x200)
                .addi(10, 0, 2)
                .addi(11, 0, 2)
                .bne(11, 10, 0x100)
                .bne(11, 0, 0x100)
                .set_origin(0x30c)
                .nop()
        ).dict


class ProofBLT(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BLT

    def run_general(self):
        last = self.time[1]
        m = self.module
        core: Core = self.uut
        comb = m.d.comb

        lhs = Signal(signed(core.xlen))
        rhs = Signal(signed(core.xlen))
        blt_res = Signal(name="blt_res")

        comb += lhs.eq(last.r[last.btype.rs1])
        comb += rhs.eq(last.r[last.btype.rs2])
        comb += blt_res.eq(lhs < rhs)

        with m.If(blt_res):
            self.assert_jump_was_taken()
        with m.Else():
            self.assert_no_jump_taken()

        lhs_bz = Signal()                       # bz = below-zero
        rhs_bz = Signal()
        comb += lhs_bz.eq(lhs[core.xlen-1])
        comb += rhs_bz.eq(rhs[core.xlen-1])

        with m.If(lhs_bz & (~rhs_bz)):
            self.assert_jump_was_taken()
        with m.Elif((~lhs_bz) & (rhs_bz)):
            self.assert_no_jump_taken()

    def simulate(self):
        return (MemBuild(0x200)
                .nop()
        ).dict


class ProofBGE(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BGE

    def run_general(self):
        last = self.time[1]
        m = self.module
        core: Core = self.uut
        comb = m.d.comb

        lhs = Signal(signed(core.xlen))
        rhs = Signal(signed(core.xlen))
        bge_res = Signal(name="bge_res")

        comb += lhs.eq(last.r[last.btype.rs1])
        comb += rhs.eq(last.r[last.btype.rs2])
        comb += bge_res.eq(lhs >= rhs)

        with m.If(bge_res):
            self.assert_jump_was_taken()
        with m.Else():
            self.assert_no_jump_taken()

        lhs_bz = Signal()                       # bz = below-zero
        rhs_bz = Signal()
        comb += lhs_bz.eq(lhs[core.xlen-1])
        comb += rhs_bz.eq(rhs[core.xlen-1])

        with m.If(lhs_bz & (~rhs_bz)):
            self.assert_no_jump_taken()
        with m.Elif((~lhs_bz) & (rhs_bz)):
            self.assert_jump_was_taken()

    def simulate(self):
        return (MemBuild(0x200)
                .nop()
        ).dict


class ProofBLTU(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BLTU

    def run_general(self):
        last = self.time[1]
        m = self.module
        core: Core = self.uut
        comb = m.d.comb

        bltu_lhs = Signal(unsigned(core.xlen))
        bltu_rhs = Signal(unsigned(core.xlen))
        bltu_res = Signal(name="bltu_res")

        comb += bltu_lhs.eq(last.r[last.btype.rs1])
        comb += bltu_rhs.eq(last.r[last.btype.rs2])
        comb += bltu_res.eq(bltu_lhs < bltu_rhs)

        with m.If(bltu_res):
            self.assert_jump_was_taken()
        with m.Else():
            self.assert_no_jump_taken()

        bltu_lhs_bz = Signal()                       # bz = below-zero in signed variant
        bltu_rhs_bz = Signal()
        comb += bltu_lhs_bz.eq(bltu_lhs[core.xlen-1])
        comb += bltu_rhs_bz.eq(bltu_rhs[core.xlen-1])

        with m.If(bltu_lhs_bz & (~bltu_rhs_bz)):
            self.assert_no_jump_taken()
        with m.Elif((~bltu_lhs_bz) & (bltu_rhs_bz)):
            self.assert_jump_was_taken()

    def simulate(self):
        return (MemBuild(0x200)
                .nop()
        ).dict

class ProofBGEU(ProofBranchBase):
    def op_branch(self):
        return OpBranch.BGEU

    def run_general(self):
        last = self.time[1]
        m = self.module
        core: Core = self.uut
        comb = m.d.comb

        lhs = Signal(unsigned(core.xlen))
        rhs = Signal(unsigned(core.xlen))
        bgeu_res = Signal(name="bgeu_res")

        comb += lhs.eq(last.r[last.btype.rs1])
        comb += rhs.eq(last.r[last.btype.rs2])
        comb += bgeu_res.eq(lhs >= rhs)

        with m.If(bgeu_res):
            self.assert_jump_was_taken()
        with m.Else():
            self.assert_no_jump_taken()

        lhs_bz = Signal()                       # bz = below-zero in signed  representation
        rhs_bz = Signal()
        comb += lhs_bz.eq(lhs[core.xlen-1])
        comb += rhs_bz.eq(rhs[core.xlen-1])

        with m.If(lhs_bz & (~rhs_bz)):
            self.assert_jump_was_taken()            
        with m.Elif((~lhs_bz) & (rhs_bz)):
            self.assert_no_jump_taken()
            

    def simulate(self):
        return (MemBuild(0x200)
                .nop()
        ).dict

