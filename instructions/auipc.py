from nmigen import Module, Signal

from instruction import Instruction
from core import Core
from encoding import UType
from opcodes import Opcode, OpImm, DebugOpcode

from proofs.auipc import ProofAuipc

class AuipcInstr(Instruction):
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return core.utype.opcode == Opcode.Auipc

    def implement(self):
        core : Core = self.core
        core.assign_gpr(core.utype.rd, core.pc + core.utype.imm)
        core.emit_debug_opcode(DebugOpcode.AUIPC, core.utype.imm)
        core.move_pc_to_next_instr()

    def proofs(self):
        return [ProofAuipc]