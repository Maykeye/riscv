from encoding import IType
from opcodes import Opcode, OpImm

class MemBuild:
    def __init__(self, pc=0x0, existing_dict=None):
        self.pc = pc
        self.dict=existing_dict or {}

    def add_i32(self, int32, pc=None):        
        """ Add word to the memory after splitting it to bytes"""
        self.pc = pc or self.pc        
        self.dict[self.pc+0] = (int32 >> (8*0)) & 0xFF
        self.dict[self.pc+1] = (int32 >> (8*1)) & 0xFF
        self.dict[self.pc+2] = (int32 >> (8*2)) & 0xFF
        self.dict[self.pc+3] = (int32 >> (8*3)) & 0xFF
        self.pc += 4
        return self

    def addi(self, rd, rs1, imm):
        """ ADDI instruction implementation """
        return self.add_i32(IType.build_i32(opcode=Opcode.OpImm, funct3=OpImm.ADD, rd=rd, rs1=rs1, imm=imm)) 

if __name__ == "__main__":
    m = MemBuild(0)
    m.add_i32(0x11223344)
    assert m.dict[0] == 0x44
    assert m.dict[1] == 0x33
    assert m.dict[2] == 0x22
    assert m.dict[3] == 0x11
