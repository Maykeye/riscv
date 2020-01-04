from nmigen import Module, Signal, ClockSignal, ClockDomain
from nmigen.cli import main_parser, main_runner, main as nmigen_main

from core import Core
from instructions.op_imm import OpImmInstr
from clock_info import ClockInfo
import sys 
import alu 

from proofs.verification import ProofAdd

def main():
    m = Module()
    clock = ClockInfo("i")
    m.domains.i = clock.domain
    m.submodules.core = core = Core()
    core.aux_ports.append(clock.clk)
    core.aux_ports.append(clock.rst)
    
    core.add_instruction(OpImmInstr())  
    p = ProofAdd()  
    p.run(m, core)

    #core.simulate(m, clock, OpImmInstr.simulate())

    if "generate" in sys.argv:
        nmigen_main(m, ports=core.ports())


if __name__ == "__main__":
    main()