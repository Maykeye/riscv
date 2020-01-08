from nmigen import Module, Signal

from instruction import Instruction
from core import Core
from opcodes import Opcode, OpImm, DebugOpcode

from proofs.jalr import ProofJalr

class JalrInstr(Instruction):
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return (core.itype.opcode == Opcode.Jalr) & (core.itype.funct3 == 0)

    def implement(self):
        core : Core = self.core
        
        core.assign_gpr(core.itype.rd, core.pc + 4)
        all_bits = (1 << core.xlen) - 1
        mask = all_bits ^ 1 #clear_lsb
        target_address = ((core.query_rs1() + core.itype.imm)[0:32]) & mask
        core.assign_pc(target_address)
        core.emit_debug_opcode(DebugOpcode.JALR, core.itype.imm)

    def proofs(self):
        return [ProofJalr]