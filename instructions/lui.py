from nmigen import Module, Signal

from instruction import Instruction
from core import Core
from encoding import UType
from opcodes import Opcode, OpImm, DebugOpcode

from proofs.lui import ProofLui

class LuiInstr(Instruction):
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return core.utype.opcode == Opcode.Lui

    def implement(self):
        core : Core = self.core
        
        core.assign_gpr(core.utype.rd, core.utype.imm)

        core.emit_debug_opcode(DebugOpcode.LUI, core.itype.imm)
        core.move_pc_to_next_instr()

    def proofs(self):
        return [ProofLui]