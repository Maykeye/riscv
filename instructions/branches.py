from nmigen import Module, Signal, Mux, Const, Value, signed, unsigned

from instruction import Instruction
from core import Core
from opcodes import Opcode, DebugOpcode, OpBranch
from proofs.branches import ProofBEQ, ProofBNE, ProofBLT, ProofBGE, ProofBLTU, ProofBGEU
from typing import List
from skeleton import as_signed

class BranchBase(Instruction):
    def comparison_impl(self, rv1:Value, rv2:Value) -> Value:
        """ Compare two values that were got from registers """
        raise Exception("not overridden in child class")
    def debug_opcodes(self) -> List[DebugOpcode]:
        """ Return two debug opcodes: [non-negated, negated] """
        raise Exception("not overridden in child class")
    def op_branch(self) -> OpBranch:
        """ Return funct3 example to extract two bits for funct3 """
        raise Exception("not overridden in child class")
    def proofs(self):
        raise Exception("not overridden in child class")
   

    def implement(self):
        core : Core = self.core
        m = core.current_module
        comb = m.d.comb
        
        # First we compare the actual values in RS1 and RS2
        eq_comparison = Signal()
        comb += eq_comparison.eq(self.comparison_impl(core.query_rs1(), core.query_rs2()))

        # Then we decide if we want to negate them
        eq_result = Signal()
        comb += eq_result.eq(Mux(core.btype.funct3[0], ~eq_comparison, eq_comparison))
    
        # With this, we can move to new pc
        with m.If(eq_result):
            core.assign_pc(core.pc + core.btype.imm)
            # Let the world know what branch instruction was executed
            core.emit_debug_opcode(self.decode_debug_opcode(), core.btype.imm)
        with m.Else():
            core.move_pc_to_next_instr()
            # Let the world know what branch instruction was executed
            core.emit_debug_opcode(self.decode_debug_opcode(), 0xFFFF_FFFF)


    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return (core.btype.opcode == Opcode.Branch) & (core.btype.funct3[1:3] == Const(self.op_branch().value >> 1, 2))


    def decode_debug_opcode(self):
        core : Core = self.core
        return Mux(core.btype.funct3[0], self.debug_opcodes()[1], self.debug_opcodes()[0])


class BeqBneInstr(BranchBase):    
    def comparison_impl(self, rv1, rv2):
        return rv1 == rv2    
    def op_branch(self):
        return OpBranch.BEQ
    def debug_opcodes(self):
        return [DebugOpcode.BEQ, DebugOpcode.BNE]
    def proofs(self):
        return [ProofBEQ, ProofBNE]


class BltBgeInstr(BranchBase):    
    def comparison_impl(self, rv1, rv2):
        core : Core = self.core
        m = core.current_module
        comb = m.d.comb

        rv1_signed = Signal(signed(core.xlen))
        rv2_signed = Signal(signed(core.xlen))
        comb += rv1_signed.eq(rv1)
        comb += rv2_signed.eq(rv2)    
        return rv1_signed < rv2_signed

    def op_branch(self):
        return OpBranch.BLT
    def debug_opcodes(self):
        return [DebugOpcode.BLT, DebugOpcode.BGE]
    def proofs(self):
        return [ProofBLT, ProofBGE]

class BltuBgeuInstr(BranchBase):    
    def comparison_impl(self, rv1, rv2):
        core : Core = self.core
        m = core.current_module
        comb = m.d.comb

        rv1_unsigned = Signal(unsigned(core.xlen))
        rv2_unsigned = Signal(unsigned(core.xlen))
        comb += rv1_unsigned.eq(rv1)
        comb += rv2_unsigned.eq(rv2)    
        return rv1_unsigned < rv2_unsigned

    def op_branch(self):
        return OpBranch.BLTU
    def debug_opcodes(self):
        return [DebugOpcode.BLTU, DebugOpcode.BGEU]
    def proofs(self):
        return [ProofBLTU, ProofBGEU]