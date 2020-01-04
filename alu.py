from nmigen import Signal, Module, Mux, Const
from typing import Optional
from nmigen.build import Platform
from skeleton import ElaboratableAbstract
from opcodes import OpAlu
from skeleton import as_signed

class ALU(ElaboratableAbstract):
    def __init__(self, xlen, pfx="", include_invalid_op=False):
        """
            xlen - number of bits for operands
            pfx - prefix in signal names, if specified, additional '_' to the end will be attached
            include_invalid_op - if True, adds output ping `invalid_op` that shows that `op` was unrecognized
        """
        super().__init__()
        if pfx:
            pfx += "_"
        self.xlen = xlen
        self.lhs = self.add_input_signal(xlen, name=f"{pfx}lhs") #rs1
        self.rhs = self.add_input_signal(xlen, name=f"{pfx}rhs") #rs2 or imm
        self.op = self.add_input_signal(OpAlu, name=f"{pfx}op")
        self.en = self.add_input_signal(name=f"{pfx}en")
        self.output = self.add_output_signal(xlen, name=f"{pfx}output")
        self.invalid_op : Optional[Signal] = self.add_output_signal(name=f"{pfx}invalid") if include_invalid_op else None
    
    def elaborate(self, p:Platform) -> Module:
        m = Module()
        comb = m.d.comb    
        signed_lhs = as_signed(m,self.lhs)
        signed_rhs = as_signed(m,self.rhs)
        with m.If(self.en):
            if self.invalid_op is not None:
                comb += self.invalid_op.eq(0)
            with m.Switch(self.op):
                with m.Case(OpAlu.ADD):                    
                    comb += self.output.eq(self.lhs + self.rhs)
                with m.Case(OpAlu.SLT):
                    comb += self.output.eq(Mux(signed_lhs < signed_rhs, 1, 0))
                with m.Case(OpAlu.SLTU):
                    comb += self.output.eq(Mux(self.lhs < self.rhs, 1, 0))
                with m.Case(OpAlu.AND):
                    comb += self.output.eq(self.lhs & self.rhs) 
                with m.Case(OpAlu.OR):
                    comb += self.output.eq(self.lhs | self.rhs) 
                with m.Case(OpAlu.XOR):
                    comb += self.output.eq(self.lhs ^ self.rhs) 
                with m.Default():
                    comb += self.output.eq(0)                
                    if self.invalid_op is not None:                    
                        comb += self.invalid_op.eq(1)
        with m.Else():
            self.output.eq(0)
        return m

##
## FORMAL VERIFICATION OF THE ALU
## 
from nmigen.asserts import Assert
from nmigen.cli import main_parser, main_runner

def __main():
    m = Module()
    xlen=32
    m.submodules.alu1 = alu1 = ALU(xlen, "A", include_invalid_op=True)
    m.submodules.alu2 = alu2 = ALU(xlen, "B")

    op = Signal(OpAlu)
    en = Signal()
    lhs=Signal(32)
    rhs=Signal(32)
    ports = [op,en,lhs,rhs]

    m.d.comb += alu1.op.eq(op)
    m.d.comb += alu2.op.eq(op)
    m.d.comb += alu1.en.eq(en)
    m.d.comb += alu2.en.eq(en)

    m.d.comb += alu1.lhs.eq(lhs)
    m.d.comb += alu1.rhs.eq(rhs)

    m.d.comb += alu2.lhs.eq(rhs)
    m.d.comb += alu2.rhs.eq(lhs)
    
      
    
    lhs_signed = as_signed(m, lhs)
    rhs_signed = as_signed(m, rhs)
    with m.If(alu1.en):
        with m.If(alu1.op == OpAlu.XOR):
            m.d.comb += Assert(alu1.invalid_op == 0)
            m.d.comb += Assert(alu1.output == alu2.output)
            m.d.comb += Assert(alu1.output == (lhs ^ rhs))
            # NOT instruction            
            with m.If(alu1.rhs == -1):                
                m.d.comb += Assert(alu1.output == ~alu1.lhs)
        with m.Elif(alu1.op == OpAlu.ADD):        
            m.d.comb += Assert(alu1.invalid_op == 0)
            m.d.comb += Assert(alu1.output == alu2.output)
            m.d.comb += Assert(alu1.output == (lhs + rhs)[:xlen])
            # MV instruction
            with m.If(alu1.rhs == 0):
                m.d.comb += Assert(alu1.output == alu1.lhs)

        with m.Elif(alu1.op == OpAlu.SLT):        
            m.d.comb += Assert(alu1.invalid_op == 0)
            with m.If(lhs_signed < rhs_signed):
                m.d.comb += Assert(alu1.output == 1)
            with m.Else():
                m.d.comb += Assert(alu1.output == 0)

        with m.Elif(alu1.op == OpAlu.SLTU):
            m.d.comb += Assert(alu1.invalid_op == 0)
            m.d.comb += Assert(alu1.output == (lhs < rhs))
            # Explicit mention of rhs = 1
            with m.If(rhs == 1):
                with m.If(alu1.output == 1):
                    m.d.comb += Assert(lhs == 0)

        with m.Elif(alu1.op == OpAlu.AND):      
            m.d.comb += Assert(alu1.invalid_op == 0)
            m.d.comb += Assert(alu1.output == alu2.output)
            m.d.comb += Assert(alu1.output == (lhs & rhs))

        with m.Elif(alu1.op == OpAlu.OR):         
            m.d.comb += Assert(alu1.invalid_op == 0)
            m.d.comb += Assert(alu1.output == alu2.output)
            m.d.comb += Assert(alu1.output == (lhs | rhs))
        with m.Else():
            m.d.comb += Assert(alu1.invalid_op)


    with m.Else():
        m.d.comb += Assert(alu1.output == 0)
        m.d.comb += Assert(alu2.output == 0)


    parser = main_parser()
    args = parser.parse_args()
    main_runner(parser, args, m, ports = ports + alu1.ports() + alu2.ports())



if __name__ == "__main__":
    __main()