from nmigen import Module, Signal, ClockSignal, ClockDomain
from nmigen.cli import main_parser, main_runner

from core import Core
from instructions.nop import NOP
from clock_info import ClockInfo

import alu 

def main():
    m = Module()
    clock = ClockInfo("i")
    m.domains.i = clock.domain
    m.submodules.core = core = Core()
    core.aux_ports.append(clock.clk)
    core.aux_ports.append(clock.rst)
    
    core.add_instruction(NOP())    
    core.simulate(m, clock, NOP.simulate())

if __name__ == "__main__":
    main()