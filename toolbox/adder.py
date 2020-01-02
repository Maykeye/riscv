import os
import re
import sys
from typing import List

from nmigen import Elaboratable, Module, Signal, signed, unsigned, Cat
from nmigen.hdl.ast import Statement, Const
from nmigen.asserts import Assert, Assume, Past
from nmigen.back.pysim import Simulator, Delay
from nmigen.build import Platform
from nmigen.cli import main_parser, main_runner

from skeleton import ElaboratableAbstract, fix_gtkw_win, dump_inputs
from skeleton import muS



class AbstractAdder(ElaboratableAbstract):
    def __init__(self, n):
        super().__init__()
        self.input_width = n        
        self.x = self.add_input_signal(n, name="x")
        self.y = self.add_input_signal(n, name="y")
        self.out = self.add_output_signal(n+1, name="out")        
        self.carry0 = self.add_input_signal(name="carry0")

    def simulate(self, m):
        adder = self
        dump_inputs(adder, m)
        sim = Simulator(m)
        def timings():
            yield adder.x.eq(0x1)
            yield adder.y.eq(0x2)
            yield Delay(1 * muS)
        
        sim.add_process(timings)
        os.chdir("waves")
        with sim.write_vcd("test.vcd", "test.gtkw",  traces = adder.ports()):
            sim.run()
        fix_gtkw_win("test.gtkw")
        
    def prove(self, m:Module):
        adder = self
        m.d.comb += Assert(adder.out == (adder.x + adder.y + adder.carry0)[:1+self.input_width])

class CarryLookAheadAdder(AbstractAdder):


    def __init__(self, n):
        super().__init__(n)

        self.generators = []
        self.propogators = []
        
    

    def elaborate_generators(self, m):
        for i in range(self.input_width):
            g = Signal(name=f"g{i}")
            p = Signal(name=f"p{i}")

            m.d.comb += g.eq(self.x[i] & self.y[i]) #generates C
            m.d.comb += p.eq(self.x[i] ^ self.y[i]) #passes C[i-1]
            self.generators.append(g)
            self.propogators.append(p)
            

    def predict_carry_out_impl(self, i : int) -> List[Statement]:
        if i == -1:
            return [self.carry0]

        terms = self.predict_carry_out_impl(i - 1)

        new_terms_carried = [self.propogators[i] & last_term for last_term in terms]
        return [self.generators[i]] + new_terms_carried

    def carry_in(self, i : int) -> Statement:
        carry_in_terms = self.predict_carry_out_impl(i-1)
        carry_in = self.build_tree_or(carry_in_terms)
        return carry_in

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        self.elaborate_generators(m)
        for i in range(self.input_width):
            m.d.comb += self.out[i].eq(self.x[i] ^ self.y[i] ^ self.carry_in(i))

        m.d.comb += self.out[self.input_width].eq(self.carry_in(self.input_width))

        return m




class RippleCarryAdder(AbstractAdder):
    def elaborate(self, platform : Platform = None):
        self.module = m = Module()        

        last_carry = self.elaborate_range(m, self.input_width, 0, self.adder_step_impl)
        m.d.comb += self.out[self.input_width].eq(last_carry)

        return m

    def adder_step_impl(self, m : Module, carry_in : Statement, step : int) -> Statement:
        carry_out = Signal(name=f"carry_out_{step}")
        lhs = self.x[step]
        rhs = self.y[step]
        m.d.comb += carry_out.eq( 0
            |   (rhs & carry_in)
            |   (lhs & carry_in)
            |   (lhs & rhs)
        )

        m.d.comb += self.out[step].eq(lhs ^ rhs ^ carry_in)

        return carry_out


    def __repr__(self):
        return "<toolbox.RippleCarryAdder%d>" % self.input_width




