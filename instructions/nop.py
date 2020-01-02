from instruction import Instruction
from core import Core
from encoding import IType
from opocodes import Opcode, OpImm, DebugOpcode
from membuild import MemBuild

class NOP(Instruction):
    # this is sample instruction, 
    # it shouldn't be used for real work
    # it just shows an example on how to add instruction to the core

    def check(self):
        core = self.core
        """ Check that instruction can be executed """
        return ((core.itype.opcode == Opcode.OpImm)
            & (core.itype.funct3 == OpImm.ADDI)
            & (core.itype.imm==0)
            & (core.itype.rs1==0)            
            & (core.itype.rd ==0))

    def implement(self):
        self.core.move_pc_to_next_instr()
        self.core.emit_debug_opcode(DebugOpcode.NOP, self.core.r.pc)

        

    @staticmethod
    def simulate():
        membuild=MemBuild(0x200)
        return (membuild
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADDI))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADDI))
            .dict)
