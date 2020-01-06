from encoding import IType, JType, UType
from opcodes import Opcode, OpImm

class MemBuild:
    def __init__(self, pc=0x0, existing_dict=None):
        self.pc = pc
        self.dict=existing_dict or {}

    def set_origin(self, new_pc):
        self.pc = new_pc
        return self

    def add_i32(self, int32):
        """ Add word to the memory after splitting it to bytes"""
        self.dict[self.pc+0] = (int32 >> (8*0)) & 0xFF
        self.dict[self.pc+1] = (int32 >> (8*1)) & 0xFF
        self.dict[self.pc+2] = (int32 >> (8*2)) & 0xFF
        self.dict[self.pc+3] = (int32 >> (8*3)) & 0xFF
        self.pc += 4
        return self

    def mv(self, rd, rs1):
        return self.addi(rd, rs1, 0)
    def addi(self, rd, rs1, imm):
        """ ADDI instruction implementation """
        return self.add_i32(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=rd, rs1=rs1, imm=imm)) 
    def jal(self, imm, rd):
        return self.add_i32(JType.build_i32(opcode=Opcode.Jal, imm=imm, rd=rd))
    def jalr(self, rd, rs1, imm):
        return self.add_i32(IType.build_i32(opcode=Opcode.Jalr, funct3=0, rd=rd, rs1=rs1, imm=imm)) 
    def j(self, imm):
        return self.jal(imm,0)
    def lui(self, rd, imm):
        return self.add_i32(UType.build_i32(Opcode.Lui, rd, imm))
    def nop(self):
        return self.mv(0, 0)
    def auipc(self, rd, imm):
        return self.add_i32(UType.build_i32(opcode=Opcode.Auipc, rd=rd, imm=imm))

if __name__ == "__main__":
    m = MemBuild(0)
    m.add_i32(0x11223344)
    assert m.dict[0] == 0x44
    assert m.dict[1] == 0x33
    assert m.dict[2] == 0x22
    assert m.dict[3] == 0x11
