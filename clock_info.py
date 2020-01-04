from nmigen import ClockDomain, ClockSignal, Signal,Module

class ClockInfo:
    def __init__(self, name):
        self.domain = ClockDomain(name)
        self.rst = Signal(name=f"clk_rst_{name}")
        self.clk = ClockSignal(name)        
        self.domain.rst = self.rst 
        self.name = f"(clock {name})"
        