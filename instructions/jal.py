from nmigen import Module, Signal

from instruction import Instruction
from core import Core
from opcodes import Opcode, OpImm, DebugOpcode

from proofs.jal import ProofJal

class JalInstr(Instruction):
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return core.jtype.opcode == Opcode.Jal

    def implement(self):
        core : Core = self.core
        
        core.assign_gpr(core.jtype.rd, core.r.pc + 4)
        core.move_pc_to_next_instr(core.jtype.imm)
        core.emit_debug_opcode(DebugOpcode.JAL, core.jtype.imm)

    def proofs(self):
        return [ProofJal]