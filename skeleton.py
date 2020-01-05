import re
import sys
from typing import List, Callable, Union, Tuple

from nmigen import Elaboratable, Module, Signal, signed, unsigned, Cat, Value
from nmigen.back.pysim import Simulator, Delay
from nmigen.hdl.ast import Statement
from nmigen.build import Platform
from nmigen.asserts import Past
from nmigen.cli import main_parser, main_runner

class ElaboratableAbstract(Elaboratable):
    
    extra_proofs = {}

    def __init__(self):
        self.input_signal_list : List[Signal] = []
        self.output_signal_list : List[Signal] = []
        self.aux_ports : List[Signal] = []
        self.module : Module = None #FILL ME IN ELEBORATE
        

    def inputs(self) -> List[Signal]:
        return [x for x in self.input_signal_list]

    def outputs(self) -> List[Signal]:
        return [x for x in self.output_signal_list]

    def ports(self) -> List[Signal]:
        return self.inputs() + self.outputs() + self.aux_ports

    def __add_input(self, signal : Signal):
        self.input_signal_list.append(signal)
        return signal

    def __add_output(self, signal : Signal):
        self.output_signal_list.append(signal)
        return signal

    def add_input_signal(self, *kw, **args):
        return self.__add_input(Signal(*kw, **args))

    def add_output_signal(self, *kw, **args):
        return self.__add_output(Signal(*kw, **args))

    def add_auxiliary_port(self, *kw, **args):
        signal = Signal(*kw, **args)
        self.aux_ports.append(signal)
        return signal


    def elaborate_range(self, m:Module, n:range, initial_value:Statement, step:Callable[[Module, Statement, int], Statement]):
        last_value = initial_value

        if type(n) is int:
            n = range(n)
        if type(n) is tuple:
            assert len(n) == 2
            n = range(n[0], n[1])

        for i in n:
            last_value = step(m, last_value, i)
        return last_value

    def build_tree_or(self, terms : List[Statement]) -> Statement:
        assert terms, "no eleemnts"

        while len(terms) > 1:
            new_terms = []
            i = 0
            while i < len(terms):
                if i + 1 < len(terms):
                    new_terms.append(terms[i] | terms[i+1])
                else:
                    new_terms.append(terms[i])
                i += 2
            terms = new_terms

        return terms[0]


    

class Adder(Elaboratable):
    def __init__(self):
        self.x = Signal(8)
        self.y = Signal(8)
        self.out = Signal(unsigned(8))

    def elaborate(self, platform : Platform = None):
        m = Module()        
        m.d.comb += self.out.eq(self.x + self.y)

        return m

    def inputs(self) -> List[Signal]:
        return [self.x, self.y]

    def outputs(self) -> List[Signal]:
        return [self.out]

    def ports(self) -> List[Signal]:
        return self.inputs() + self.outputs()

    def __repr__(self):
        return "<module.Adder888>"


def fix_gtkw_win(fname):
    lines = open(fname).readlines()
    
    lines[0] = re.sub(r'/mnt/(.)/', r'\1:/', lines[0])
    fname = re.sub(r'\.gtkw$',r'_win.gtkw',fname)
    with open(fname, "w") as res:
        res.writelines(lines)

def dump_inputs(from_module:Module, to_module : Module, prefix="", suffix="") -> List[Signal]:
    input_copies = []
    for signal in from_module.inputs():
        if signal.__class__ == Signal:
            new_signal = Signal(shape=signal.shape(), name=prefix+signal.name+suffix, attrs=signal.attrs, decoder=signal.decoder)
            to_module.d.comb += new_signal.eq(signal)
            input_copies.append(new_signal)
        else:
            raise Exception("Unsupported signal %s type %s" % (signal, signal.__class__))
    return input_copies


def bit_slice(n : int, hi:int, lo:int):
    """ returns n[hi:lo] bits (inclusive hi and lo)"""
    if isinstance(n, Value):
        _n : Value = n
        return _n.bit_select(lo, (hi-lo)+1)

    shifted = n >> lo 
    width = hi - lo + 1
    mask = (1 << width) - 1
    bits = shifted & mask
    return bits

def as_signed(m : Module, signal:Signal):
    """ Create a new copy of signal, but marked as signed """
    if signal.signed:
        # signed already 
        print(f"Warning: trying to cast already signed sigan {signal.name}")
        return signal 
    
    new_signal = Signal(signed(signal.width), name=signal.name+"_signed")
    m.d.comb += new_signal.eq(signal)
    return new_signal


def SeqPast(signal : Signal, hi : int, lo:int, expect : bool):
    """ Chain Past(x, hi) & Past(x, hi-1)...& Past(x, lo) or ~Past(x, hi) & ~Past(x, hi-1)...& ~Past(x, lo)"""
    def make_term():
        if expect:
            return Past(signal, n)
        else:
            return ~Past(signal, n)

    assert hi >= lo
    n = hi
    term = make_term()
    n -= 1
    while n >= lo:
        term = term & make_term()
        n -= 1
    return term

muS=1e-6

def repeat_bit(bit, n) -> Statement:
    return Cat([bit for _ in range(n)])

if __name__ == "__main__":
    parser = main_parser()    
    args = parser.parse_args()

    m = Module()
    m.submodules.adder = adder = Adder()
    x = Signal(8)
    y = Signal(8)
    m.d.comb += adder.x.eq(x)
    m.d.comb += adder.y.eq(y)
    sim = Simulator(m)

    def timings():
        yield adder.x.eq(0x00)
        yield adder.y.eq(0x00)
        yield Delay(muS)

        yield adder.x.eq(0xFF)
        yield adder.y.eq(0xFF)
        yield Delay(muS)        

        yield adder.x.eq(0x00)
        yield Delay(muS)

    sim.add_process(timings)
    with sim.write_vcd("test.vcd", "test.gtkw",  traces = [x,y]+adder.ports()):
        sim.run()
    fix_gtkw_win("test.gtkw")
    

    
    #main_runner(parser, args, m, ports=[]+adder.ports())

#if __name__ == "__main__":
#    parser = main_parser()    
#    args = parser.parse_args()
#    m = Module()
#    m.submodules.adder = adder = Adder()
#    
#    main_runner(parser, args, m, ports=[]+adder.ports())
