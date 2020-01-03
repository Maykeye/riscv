from nmigen import Module, Signal

from instruction import Instruction
from core import Core
from encoding import IType
from opocodes import Opcode, OpImm, DebugOpcode
from nmigen import Mux
from membuild import MemBuild




class OpImmInstr(Instruction):
    
    # Bit in imm (not whole word) that shows that shift is arithmethic
    IMM_SHR_ARITH_BIT=10

    def check(self):
        core = self.core
        """ Check that instruction can be executed """
        return core.itype.opcode == Opcode.OpImm

    def implement(self):
        

        m : Module = self.core.current_module
        core : Core = self.core
                
        shift_amout = core.itype.imm[0:5]
        with m.Switch(core.itype.funct3):
            # TODO: report error if imm_hi is neither 0 nor ([10]=1 with [rest]=0)
            with m.Case(OpImm.SHIFT_LEFT):
                core.call_left_shift(core.r[core.itype.rd], core.r[core.itype.rs1], shift_amout)
            with m.Case(OpImm.SHIFT_RIGHT):
                core.call_right_shift(core.r[core.itype.rd], core.r[core.itype.rs1], shift_amout,
                    core.r[core.itype.rs1][core.xlen-1] & core.itype.imm[OpImmInstr.IMM_SHR_ARITH_BIT])

            with m.Default():
                core.call_alu(core.r[core.itype.rd], core.itype.funct3, core.r[core.itype.rs1], core.itype.imm)
        
        self.core.emit_debug_opcode(self.decode_debug_opcode(), self.core.r.pc)
        self.core.move_pc_to_next_instr()

    def decode_debug_opcode(self) -> Signal:
        m : Module = self.core.current_module
        comb = m.d.comb
        core : Core = self.core

        if core.debug_opcode is None:
            return DebugOpcode.UNREACHABLE
        debug_value = Signal(DebugOpcode, name="imm_dbg")
        with m.Switch(core.itype.funct3):
            with m.Case(OpImm.SHIFT_RIGHT):
                with m.If(core.itype.imm[OpImmInstr.IMM_SHR_ARITH_BIT]):
                    comb += debug_value.eq(DebugOpcode.SRA_imm)
                with m.Else():
                    comb += debug_value.eq(DebugOpcode.SRL_imm)


            for imm, debug_literal in [
                    (OpImm.ADD, DebugOpcode.ADD_imm), 
                    (OpImm.AND, DebugOpcode.AND_imm),
                    (OpImm.OR, DebugOpcode.OR_imm), 
                    (OpImm.XOR, DebugOpcode.XOR_imm),
                    (OpImm.SLT, DebugOpcode.SLT_imm),
                    (OpImm.SLTU, DebugOpcode.SLTIU_imm),
                    (OpImm.SHIFT_LEFT, DebugOpcode.SLL_imm)
            ]:
                with m.Case(imm): comb += debug_value.eq(debug_literal)
            
        return debug_value
                

        
        

    @staticmethod
    def simulate():

        return (MemBuild(0x200)
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=1, imm=11))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=0, imm=15))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SHIFT_LEFT,  rd=2, rs1=1, imm=2))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SHIFT_RIGHT, rd=3, rs1=2, imm=2))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SLT, rd=4, rs1=2, imm=1000))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SLT, rd=4, rs1=2, imm=0))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.XOR, rd=5, rs1=1, imm=-1))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=6, imm=6))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.AND, rd=7, rs1=6, imm=3))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=8, imm=3))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.OR, rd=9, rs1=8, imm=8))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SHIFT_RIGHT, rd=10, rs1=5, imm=1))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.SHIFT_RIGHT, rd=10, rs1=5, imm=1 | (1 << 10)))
            .add(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD))
            .dict
        )

          

        