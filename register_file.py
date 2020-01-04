from nmigen import Signal, Array

class RegisterFile:
    """ Register file that contains all registers of the CPU"""
    N = 32
    def __init__(self, xlen, prefix=""):
        if prefix:
            prefix += "_"
        self.r = Array([Signal(xlen, name=f"{prefix}x{i}") for i in range(RegisterFile.N)])
        self.pc = Signal(xlen, name=f"{prefix}pc")

    def main_gpr_count(self):
        """ Number of unique GPRs(i.e. gpr that don't alias other gprs) """
        return len(self.r)

    def __getitem__(self, key):
        return self.r[key]
