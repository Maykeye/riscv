import os
from nmigen import Module, Signal
from nmigen.asserts import Assert
from nmigen.hdl.ast import Statement, Const
from nmigen.build import Platform
from nmigen.back.pysim import Simulator, Delay

from skeleton import ElaboratableAbstract
from skeleton import dump_inputs, fix_gtkw_win
from skeleton import muS

class ParityBase(ElaboratableAbstract):

    def __init__(self, n):
        super().__init__()
        self.input_width = n        
        self.a = self.add_input_signal(n, name="a")
        self.parity = self.add_output_signal(name="parity")

    def prove(self, m : Module):
        last = 0
        sum_of_bits = self.add_output_signal(self.input_width, name="sum")
        for i in range(self.input_width):
            next_value = Signal(self.input_width)
            m.d.comb += next_value.eq(last + self.a[i])
            last = next_value
        m.d.comb += sum_of_bits.eq(next_value)
        
        with m.If((sum_of_bits % 2) == 0): #even
            m.d.comb += Assert(self.parity == Const(1, 1))
        with m.If((sum_of_bits % 2) == 1): #odd
            m.d.comb += Assert(self.parity == Const(0, 1))

    def simulate(self, m:Module):
        uut = self
        dump_inputs(uut, m)
        sim = Simulator(m)
        def timings():
            yield uut.a.eq(0x3)            
            yield Delay(1 * muS)
            yield uut.a.eq(0x4)            
            yield Delay(1 * muS)
            yield uut.a.eq(0x5)
            yield Delay(1 * muS)
            yield uut.a.eq(0x7)
            yield Delay(1 * muS)
        
        sim.add_process(timings)
        os.chdir("waves")
        with sim.write_vcd("test.vcd", "test.gtkw",  traces = uut.ports()):
            sim.run()
        fix_gtkw_win("test.gtkw")

class ParitySeq(ParityBase):
    def __init__(self, n):
        super().__init__(n)
        assert n > 1

    def elaborate(self, platform:Platform) -> Module:
        m = Module()


        def step(m:Module, last : Statement, index : int) -> Statement:
            parity = Signal(name=f"parity_{index}")
            m.d.comb += parity.eq(last ^ self.a[index])            
            return parity
        
        all_xored = self.elaborate_range(m, self.input_width, 0, step)
        m.d.comb += self.parity.eq(~all_xored)
        return m
    

class ParityTree(ParityBase):
    def __init__(self, n):
        super().__init__(n)
        assert n > 1        
        assert (n & (n - 1)) == 0, "N must be a power of 2"

    def elaborate(self, platform:Platform) -> Module:
        m = Module()

        inputs = [self.a[i] for i in range(self.input_width)]
        h = 0
        while len(inputs) > 1:
            h += 1
            outputs = []
            i = 0
            while i < len(inputs):
                s = Signal(name = f"p{h}_{i}")
                m.d.comb += s.eq(inputs[i] ^ inputs[i+1])
                i += 2
                outputs.append(s)
            inputs = outputs
        m.d.comb += self.parity.eq(~inputs[0])
        return m
