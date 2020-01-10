from nmigen import Signal
class MemoryBus:

    def __init__(self, alen, xlen, prefix=""):
        if prefix:
            prefix = f"{prefix}_"

        # Address from which memory must be read
        self.addr = Signal(alen, name=f"{prefix}addr")

        # Enable signal shows that core wants to read data from memory on address addr
        self.en = Signal(name=f"{prefix}en")
        
        # seq indicates that port is going to be read/write  data in sequence.
        # I.e. user thinks that next enabled address will be in extremely close
        # vicinity of the current address (0..4 bytes apart)
        self.seq = Signal(name=f"{prefix}_seq")

        # Value that is beging read from/sent to 
        #TODO: allow several values
        self.value = Signal(xlen, name=f"{prefix}_value")

        # for read bus - value was succesfully read
        # for write bus - value was succesfully written
        self.ready = Signal()

    def init_read(self, d, addr, seq=0):
        d += self.en.eq(1)
        d += self.addr.eq(addr)
        d += self.seq.eq(seq)
