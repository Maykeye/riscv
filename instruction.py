from nmigen import Module
from typing import List, Type

class Instruction:
    def __init__(self, core:'Core' = None):
        self.core : 'riscv.core.Core' = core
    
    def implement(self):
        """ Elaborate implementation of the instruction """
        pass

    def check(self):
        """ Check that instruction can be executed """
        return 0    

    def proofs(self) -> List[Type['ProofOverTicks']]:
        """ Return list of formal proofs associated with the instruction """
        pass
