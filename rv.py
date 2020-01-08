from nmigen import Module, Signal, ClockSignal, ClockDomain
from nmigen.cli import main_parser, main_runner

from core import Core

from instructions.op_imm import OpImmInstr
from instructions.jal import JalInstr
from instructions.jalr import JalrInstr
from instructions.lui import LuiInstr
from instructions.auipc import AuipcInstr
from instructions.branches import BeqBneInstr, BltBgeInstr, BltuBgeuInstr
from instructions.load import LbLbuInstr

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


    # RV32I
    core.add_instruction(OpImmInstr())
    core.add_instruction(JalrInstr())
    core.add_instruction(JalInstr())
    core.add_instruction(LuiInstr())
    core.add_instruction(AuipcInstr())
    core.add_instruction(BeqBneInstr())
    core.add_instruction(BltBgeInstr())
    core.add_instruction(BltuBgeuInstr())
    core.add_instruction(LbLbuInstr())
    
    proof_instance=None
    generate_proof="generate" in sys.argv
    all_proofs = [proof 
                    for instruction in core.instructions
                    for proof in instruction.proofs() ]
    
    if required_proof:
        for proof_class in all_proofs:
            proof_name = proof_class.__name__.lower()
            if proof_name.startswith("proof"):
                proof_name=proof_name[len("proof"):]            
            
            if required_proof == "ALL" or proof_name == required_proof:
                proof_instance = proof_class()
                if generate_proof:
                    proof_instance.run(m, core)
    if required_proof is not None and not proof_instance:
        raise Exception(f"Unknown proof {required_proof}")
        

    if "generate" in sys.argv:
        main_runner(parser, args, m, ports=core.ports())
    else:
        assert proof_instance, "use --proof proof to run simulation from proof/instruction"
        core.simulate(m, clock, proof_instance.simulate())


if __name__ == "__main__":
    main()    