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
        m : Module = self.core.current_module
        core : Core = self.core
        
        with m.If(core.jtype.rd != 0):
            return_address = (core.r.pc + 4)[:core.xlen]
            core.assign_gpr(core.jtype.rd, return_address)
        core.move_pc_to_next_instr(core.jtype.imm+4)
        core.emit_debug_opcode(DebugOpcode.JAL, core.jtype.imm)

    def proofs(self):
        return [ProofJal]