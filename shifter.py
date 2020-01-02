from typing import Union

from nmigen import Module, Signal, Const, Cat, signed
from nmigen.build import Platform
from skeleton import ElaboratableAbstract


class Shifter(ElaboratableAbstract):
    LEFT="shl"
    RIGHT="shr"

    def __init__(self, xlen : int, direction : str, prefix=""):
        super().__init__()
        if prefix: prefix += "_"
        self.prefix = prefix
        assert direction in [Shifter.LEFT, Shifter.RIGHT], "Direction may be only Shifter.LEFT or Shifter.RIGHT"

        self.direction = direction
        self.xlen = xlen 
        

        self.input = self.add_input_signal(xlen, name=f"{prefix}input")
        self.shamt = self.add_input_signal(xlen.bit_length() - 1, name=f"{prefix}shamt")
        if direction == Shifter.RIGHT:
            self.msb = self.add_input_signal(name=f"{prefix}msb")

        self.output = self.add_output_signal(xlen, name=f"{prefix}output")


    def elaborate(self, p:Platform) -> Module:
        m = Module()
        if self.direction == Shifter.LEFT:
            self.elaborate_left(m)
        elif self.direction == Shifter.RIGHT:
            self.elaborate_right(m)
        else:
            assert False, "Invalid direction. Expected LEFT/RIGHT"
        return m

    def elaborate_left(self, m:Module):
        comb = m.d.comb
        last_round = self.input
        for i in range(self.xlen.bit_length()-1):
            next_round = Signal(self.xlen, name=f"{self.prefix}_l{i}")
            with m.If(self.shamt[i]):
                comb += next_round.eq(last_round << 2**i)
            with m.Else():
                comb += next_round.eq(last_round)
            last_round = next_round

        comb += self.output.eq(last_round)

    def elaborate_right(self, m:Module):
        comb = m.d.comb
        last_round = self.input
        for i in range(self.xlen.bit_length()-1):
            next_round = Signal(self.xlen, name=f"{self.prefix}_r{i}")
            with m.If(self.shamt[i]):
                # 00 AAAA
                # 01 0AAA
                # 10 00AA
                # 11 000A


                shift_by = 2**i
                shift_end = self.xlen - shift_by

                comb += next_round[0:shift_end].eq(last_round >> shift_by)
                comb += next_round[shift_end:self.xlen].eq(Cat([self.msb for _ in range(shift_by)]))


            with m.Else():
                comb += next_round.eq(last_round)
            last_round = next_round

        comb += self.output.eq(last_round)

         

        return
#
# FORMAL VERIFICATION
#     
from nmigen.asserts import Assert, Cover
from nmigen.cli import main as nmigen_main
from skeleton import as_signed

def __verify_left(m):
    m.submodules.shl = shl = Shifter(32, Shifter.LEFT, "shl")
    comb = m.d.comb
    expect = Signal(32)
    comb += expect.eq(shl.input << shl.shamt)
    comb += Assert(shl.output == expect)
    with m.If(shl.input == 0):
        comb += Assert(shl.output == shl.input)
    with m.If(shl.shamt == 31):
        comb += Assert(shl.output[31] == shl.input[0])
    comb += Assert(shl.output[31] == shl.input.bit_select(31-shl.shamt,1))
    return shl.ports()

def __verify_right(m):
    m.submodules.shr = shr = Shifter(32, Shifter.RIGHT, "shr")
    comb = m.d.comb
    
    
    input_with_msb = Signal(signed(33))
    expected = Signal(32)
    comb += input_with_msb[0:32].eq(shr.input)
    comb += input_with_msb[32].eq(shr.msb)
    comb += expected.eq(input_with_msb >> shr.shamt)
    comb += Assert(shr.output == expected)
    with m.If(shr.shamt == 0):
        comb += Assert(shr.output == shr.input)
    with m.If((shr.input == 0) & (shr.output != 0)):
        comb += Assert(shr.msb)
    with m.If(shr.shamt == 31):
        comb += Assert(shr.output[0] == shr.input[31])
    comb += Assert(shr.output[0] == shr.input.bit_select(shr.shamt,1))

    with m.If(shr.msb == shr.input[31]):
        comb += Assert(shr.output == as_signed(m, shr.input) >> shr.shamt)
        


    return shr.ports()


def __main():
    m=Module()
    ports = []
    ports += __verify_left(m)
    ports += __verify_right(m)
    #comb += Cover((shl.input == 0x10203040) & (shl.shamt == 8))
    nmigen_main(m, ports=ports)
    
if __name__ == "__main__":
    __main()