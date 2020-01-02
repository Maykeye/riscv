from nmigen import Module

from instruction import Instruction
from core import Core
from encoding import IType
from opocodes import Opcode, OpImm, DebugOpcode
from nmigen import Mux




class NOP(Instruction):
    # this is sample instruction, 
    # it shouldn't be used for real work
    # it just shows an example on how to add instruction to the core

    def check(self):
        core = self.core
        """ Check that instruction can be executed """
        return core.itype.opcode == Opcode.OpImm

    def implement(self):

        m : Module = self.core.current_module
        core : Core = self.core
                
        shift_amout = core.itype.imm[0:5]
        with m.Case(core.itype.funct3):
            with m.Case(OpImm.SHIFT_LEFT):
                core.call_left_shift(core.r[core.itype.rd], core.r[core.itype.rs1], shift_amout)
            with m.Case(OpImm.SHIFT_RIGHT):
                core.call_right_shift(core.r[core.itype.rd], core.r[core.itype.rs1], shift_amout,
                    core.r[core.itype.rs1][core.xlen-1] & core.itype.imm[10])

            with m.Default():
                core.call_alu(core.r[core.itype.rd], core.itype.funct3, core.r[core.itype.rs1], core.itype.imm)
        
        self.core.emit_debug_opcode(DebugOpcode.NOP, self.core.r.pc)
        self.core.move_pc_to_next_instr()

        

    @staticmethod
    def simulate():
        return {
            0x200: 0x13,
            0x201: 0x00,
            0x202: 0x00,
            0x203: 0x00,

            0x204: 0x13,
            0x205: 0x00,
            0x206: 0x00,
            0x207: 0x00,

        }