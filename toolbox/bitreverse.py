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


def BitReverse__proof_identity():
    """ REV[REV[X]] === X """
    m = Module()
    m.submodules.rev_ab = rev_ab = BitReverse(4)
    m.submodules.rev_ba = rev_ba = BitReverse(4)
    inputs = []
    for i in range(rev_ab.input_width):
        input_signal = Signal(name=f"i{i}")
        inputs.append(input_signal)
        m.d.comb += rev_ab.a[i].eq(input_signal)
        m.d.comb += rev_ba.a[i].eq(rev_ab.output[i])
        m.d.comb += Assert(rev_ba.output[i] == input_signal)
    return m, inputs


class BitReverse(ElaboratableAbstract):
    extra_proofs = {'identity':BitReverse__proof_identity}

    def __init__(self, n):
        super().__init__()
        self.input_width = n        
        self.a = self.add_input_signal(n, name="a")        
        self.output = self.add_output_signal(n, name="out")

    def elaborate(self, p : Platform) -> Module:
        m = Module()
        def step(m, _, i):
            m.d.comb += self.output[i].eq(self.a[self.input_width - 1 - i])

        self.elaborate_range(m, self.input_width, 0, step)
        return m

    def prove(self, m):
        reversed_signals = [self.output[i] for i in reversed(range(self.input_width))]
        for i in range(self.input_width):
            m.d.comb += Assert(self.a[i] == reversed_signals[i])

    def simulate(self, m):
        pass


