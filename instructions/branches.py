from nmigen import Module, Signal, Mux, Const, Value

from instruction import Instruction
from core import Core
from opcodes import Opcode, DebugOpcode, OpBranch
from proofs.branches import ProofBEQ
from typing import List

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
        comb += eq_comparison.eq(self.comparison_impl(core.r[core.btype.rs1], core.r[core.btype.rs2]))

        # Then we decide if we want to negate them
        eq_result = Signal()
        comb += eq_result.eq(Mux(core.btype.funct3[0], ~eq_comparison, eq_comparison))
    
        # With this, we can move to new pc
        with m.If(eq_result):
            core.assign_pc(core.r.pc + core.btype.imm)
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
        m = core.current_module
        with m.If(core.btype.funct3[2] == 0):
            return self.debug_opcodes()[0]
        return self.debug_opcodes()[1]


class BeqBneInstr(BranchBase):    
    def comparison_impl(self, rv1, rv2):
        return rv1 == rv2    
    def op_branch(self):
        return OpBranch.BEQ
    def debug_opcodes(self):
        return [DebugOpcode.BEQ, DebugOpcode.BNE]
    def proofs(self):
        return [ProofBEQ]