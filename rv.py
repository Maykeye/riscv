from nmigen import Module, Signal, ClockSignal, ClockDomain
from nmigen.cli import main_parser, main_runner

from core import Core
from instructions.op_imm import OpImmInstr
from clock_info import ClockInfo
import sys 
import alu 
from nmigen import ResetSignal

from proofs.verification import ProofOverTicks

def main():
    m = Module()
    clock = ClockInfo("i")
    m.domains.i = clock.domain
    m.submodules.core = core = Core(clock)
    core.aux_ports.append(clock.clk)
    core.aux_ports.append(clock.rst)
    
    parser = main_parser()
    parser.add_argument("--proof", type=str, help="generate signle proof")
    args=parser.parse_args()
    required_proof = args.proof
    proof_generated=False


    instr = core.add_instruction(OpImmInstr())
    for proof_class in instr.proofs():        
        
        proof_name = proof_class.__name__.lower()
        if proof_name.startswith("proof"):
            proof_name=proof_name[len("proof"):]            
        if required_proof is None or proof_name == args.proof:
            proof_class().run(m, core)
            proof_generated=True
    if required_proof is not None and not proof_generated:
        raise Exception(f"Unknown proof {required_proof}")

    #core.simulate(m, clock, OpImmInstr.simulate())

    if "generate" in sys.argv:
        main_runner(parser, args, m, ports=core.ports())


if __name__ == "__main__":
    main()    