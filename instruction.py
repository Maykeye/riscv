from nmigen import Module

class Instruction:
    def __init__(self, core:'Core' = None):
        self.core : 'riscv.core.Core' = core
    
    def implement(self):
        """ Elaborate implementation of the instruction """
        pass

    def proof(self):
        """ Elaborate formal verification of the instruction """
        pass

    def check(self):
        """ Check that instruction can be executed """
        return 0
