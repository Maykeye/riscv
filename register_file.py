from nmigen import Signal, Array, Module
from nmigen.build import Platform
from skeleton import ElaboratableAbstract

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

class RegisterFileModule(ElaboratableAbstract):
    def __init__(self, xlen):
        super().__init__()
        self.rs1_in = self.add_input_signal(5, name="rs1_in")
        self.rs2_in = self.add_input_signal(5, name="rs2_in")
        self.rs1_out = self.add_output_signal(xlen, name="rs1_out")
        self.rs2_out = self.add_output_signal(xlen, name="rs2_out")
        
        self.rd = self.add_input_signal(5, name="rd")
        self.rd_value = self.add_input_signal(xlen, name="rd_value")


        self.r = RegisterFile(xlen) #PC not used

    def elaborate(self, p:Platform)->Module:
        m = Module()
        comb = m.d.comb
        iclk = m.d.i
        comb += self.rs1_out.eq(self.r[self.rs1_in])
        comb += self.rs2_out.eq(self.r[self.rs2_in])
        
        with m.If(self.rd != 0):
            iclk += self.r[self.rd].eq(self.rd_value)

        return m
    

from nmigen.cli import main as nmigen_main
from nmigen.asserts import Assert, Past
from skeleton import dump_inputs
from clock_info import ClockInfo

def __main():
    m = top = Module()
    clock = ClockInfo("i")
    m.domains.i = clock.domain

    top.submodules.regs = regs = RegisterFileModule(32)
    regs.aux_ports.append(clock.clk)
    regs.aux_ports.append(clock.rst)
    
    comb = m.d.comb

    with m.If(regs.rs1_in == 0):
        comb += Assert(regs.rs1_out == 0)
    with m.If(regs.rs2_in == 0):
        comb += Assert(regs.rs2_out == 0)

    with m.If(regs.rs2_in == regs.rs1_in):
        comb += Assert(regs.rs2_out == regs.rs2_out)

            
    with m.If((Past(regs.rd) == regs.rs1_in) & (~Past(clock.rst) & (~clock.rst))):
        with m.If(regs.rs1_in != 0):
            comb += Assert(regs.rs1_out == Past(regs.rd_value))


    nmigen_main(top, ports=regs.ports())




if __name__ == "__main__":
    __main()