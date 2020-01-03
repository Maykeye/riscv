class MemBuild:
    def __init__(self, pc=0x0, existing_dict=None):
        self.pc = pc
        self.dict=existing_dict or {}

    def add(self, int32, pc=None):
        self.pc = pc or self.pc
        """ Add word to the memory """
        self.dict[self.pc+0] = (int32 >> (8*0)) & 0xFF
        self.dict[self.pc+1] = (int32 >> (8*1)) & 0xFF
        self.dict[self.pc+2] = (int32 >> (8*2)) & 0xFF
        self.dict[self.pc+3] = (int32 >> (8*3)) & 0xFF
        self.pc += 4
        return self


if __name__ == "__main__":
    m = MemBuild(0)
    m.add(0x11223344)
    assert m.dict[0] == 0x44
    assert m.dict[1] == 0x33
    assert m.dict[2] == 0x22
    assert m.dict[3] == 0x11
