class MemBuild:
    def __init__(self, pc=0x0, existing_dict=None):
        self.pc = pc
        self.dict=existing_dict or {}

    def add(self, int32, pc=None):
        self.pc = pc or self.pc
        """ Add word to the memory """
        self.dict[self.pc+0] = (int32 >> 8*0) & 0xFF
        self.dict[self.pc+1] = (int32 >> 8*1) & 0xFF
        self.dict[self.pc+2] = (int32 >> 8*2) & 0xFF
        self.dict[self.pc+3] = (int32 >> 8*3) & 0xFF
        self.pc += 4
        return self
