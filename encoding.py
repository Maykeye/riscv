from typing import List
from nmigen import Signal, Cat, Const
from nmigen.hdl.ast import Statement

# for verification
from nmigen import Module
from nmigen.asserts import Assert
from nmigen.cli import main_parser, main_runner

class RType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.rd = Signal(5,name=f"{prefix}rd")
        self.funct3 = Signal(3,name=f"{prefix}funct3")
        self.rs1 = Signal(5,name=f"{prefix}rs1")
        self.rs2 = Signal(5,name=f"{prefix}rs2")
        self.funct7 = Signal(7,name=f"{prefix}funct7")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.rd.eq(input[7:12])
        comb += self.funct3.eq(input[12:15])
        comb += self.rs1.eq(input[15:20])
        comb += self.rs2.eq(input[20:25])
        comb += self.funct7.eq(input[25:32])

        
class IType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.rd = Signal(5,name=f"{prefix}rd")
        self.funct3 = Signal(3,name=f"{prefix}funct3")
        self.rs1 = Signal(5,name=f"{prefix}rs1")
        self.imm = Signal(32,name=f"{prefix}imm12")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.rd.eq(input[7:12])
        comb += self.funct3.eq(input[12:15])
        comb += self.rs1.eq(input[15:20])
        comb += self.imm.eq(Cat(input[20:32], [input[31] for _ in range(20)]))

    @staticmethod
    def build_i32(opcode:int=0, rd:int=0, funct3:int=0,rs1:int=0, imm:int=0, ensure_ints=True)->int:        
        if type(imm) == int:
            assert -2**12 <= imm < 2**12
        imm = imm & (2**12)-1

        word = opcode | (rd << 7) | (funct3 << 12) | (rs1 << 15) | (imm << 20)
        return word

        
class SType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.funct3 = Signal(3,name=f"{prefix}funct3")
        self.rs1 = Signal(5,name=f"{prefix}rs1")
        self.rs2 = Signal(5,name=f"{prefix}rs2")
        self.imm = Signal(12,name=f"{prefix}imm")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.funct3.eq(input[12:15])
        comb += self.rs1.eq(input[15:20])
        comb += self.rs2.eq(input[20:25])
        comb += self.imm.eq(Cat(input[7:12], input[25:32]))

        
class UType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.rd = Signal(5,name=f"{prefix}rd")
        self.imm = Signal(32,name=f"{prefix}imm")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.rd.eq(input[7:12])
        comb += self.imm.eq(Cat(Const(0, 12), input[12:32]))
    
        
class BType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.funct3 = Signal(3,name=f"{prefix}funct3")
        self.rs1 = Signal(5,name=f"{prefix}rs1")
        self.rs2 = Signal(5,name=f"{prefix}rs2")
        self.imm = Signal(13,name=f"{prefix}imm3")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.funct3.eq(input[12:15])
        comb += self.rs1.eq(input[15:20])
        comb += self.rs2.eq(input[20:25])
        comb += self.imm.eq(Cat(Const(0,1), input[8:12], input[25:31], input[7], input[31]))

        
class JType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.rd = Signal(5,name=f"{prefix}rd")
        self.imm = Signal(32,name=f"{prefix}imm")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.rd.eq(input[7:12])
        comb += self.imm.eq(Cat(Const(0, 1), input[21:31], input[20], input[12:20], input[31]))
    



class __Verify:    
    def build_signal(self, m, name, items) -> Signal:
        s = Signal(32, name=name)

        for item in items:
            start, end, bits = item        
            assert len(bits) == end-start+1, "Invalid item %s" % (item,)
            i = end 
            for bit in bits:
                m.d.comb += s[i].eq(1 if bit == '1' else 0)
                i -= 1


        return s

    def verify_rtype(self, m):
        sig = self.build_signal(m, "R", [(0,6,"1001011"), (7,11, "10000"), (12,14,"001"), (15, 19, "00010"), (20,24,"00011"), (25,31, "0111111")])
        r = RType("rtype")
        r.elaborate(m.d.comb, sig)
        m.d.comb += Assert(r.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(r.rd == Const(0b10000, 5))
        m.d.comb += Assert(r.funct3 == Const(1, 3))
        m.d.comb += Assert(r.rs1 == Const(2, 5))
        m.d.comb += Assert(r.rs2 == Const(3, 5))
        m.d.comb += Assert(r.funct7 == Const(0b0111111, 7))

    def verify_itype(self, m):
        sig = self.build_signal(m, "I", [(0,6,"1001011"), (7,11, "10000"), (12,14,"001"), (15, 19, "00010"), (20,31,"000110111111")])
        i = IType("itype.z")
        i.elaborate(m.d.comb, sig)
        m.d.comb += Assert(i.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(i.rd == Const(0b10000, 5))
        m.d.comb += Assert(i.funct3 == Const(1, 3))
        m.d.comb += Assert(i.rs1 == Const(2, 5))
        m.d.comb += Assert(i.imm == Const(0b000110111111, 12))

        sig = self.build_signal(m, "I", [(0,6,"1001011"), (7,11, "10000"), (12,14,"001"), (15, 19, "00010"), (20,31,"100110111111")])
        i = IType("itype.s")
        i.elaborate(m.d.comb, sig)
        m.d.comb += Assert(i.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(i.rd == Const(0b10000, 5))
        m.d.comb += Assert(i.funct3 == Const(1, 3))
        m.d.comb += Assert(i.rs1 == Const(2, 5))
        m.d.comb += Assert(i.imm == Const(0b11111111111111111111100110111111, 32))


        i_builder_check = Signal(32)
        i_builder_opcode = Signal(7)
        i_builder_rd = Signal(5)
        i_builder_funct3 = Signal(3)
        i_builder_rs1 = Signal(5)
        i_builder_imm = Signal(11)


        built_itype = IType.build_i32(i_builder_opcode, i_builder_rd, i_builder_funct3, i_builder_rs1, i_builder_imm, ensure_ints=False)
        m.d.comp += i_builder_check.eq(built_itype)
        i = IType("itype.s")
        i.elaborate(m.d.comb, built_itype)
        m.d.comb += Assert(i_builder_opcode == i.opcode)
        m.d.comb += Assert(i_builder_rd == i.rd)
        m.d.comb += Assert(i_builder_funct3 == i.funct3)
        m.d.comb += Assert(i_builder_rs1 == i.rs1)        
        m.d.comb += Assert(i_builder_imm == i.imm[0:12])
        return [i_builder_check, i_builder_opcode, i_builder_rd, i_builder_funct3, i_builder_rs1, i_builder_imm]


    def verify_stype(self, m):
        sig = self.build_signal(m, "S", [(0,6,"1001011"), (7,11, "10000"), (12,14,"001"), (15, 19, "00010"), (20,24,"00011"), (25,31, "0111111")])
        s = SType("stype")
        s.elaborate(m.d.comb, sig)
        m.d.comb += Assert(s.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(s.funct3 == Const(1, 3))
        m.d.comb += Assert(s.rs1 == Const(2, 5))
        m.d.comb += Assert(s.rs2 == Const(3, 5))
        m.d.comb += Assert(s.imm == Const(0b011111110000, 12))

    def verify_btype(self, m):
        sig = self.build_signal(m, "B", [(0,6,"1001011"), (7,7, "1"), (8,11,"0000"), (12,14,"001"), (15, 19, "00010"), (20,24,"00011"), 
            (25,30, "011111"), (31,31,"1")])
        b = BType("btype")
        b.elaborate(m.d.comb, sig)
        m.d.comb += Assert(b.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(b.funct3 == Const(1, 3))
        m.d.comb += Assert(b.rs1 == Const(2, 5))
        m.d.comb += Assert(b.rs2 == Const(3, 5))
        m.d.comb += Assert(b.imm == Const(0b1101111100000, 13))

     
    def verify_utype(self, m):
        sig = self.build_signal(m, "U", [(0,6,"1001011"), (7,11, "10000"), (12,31,"00100010000110111111")])
        u = UType("utype")
        u.elaborate(m.d.comb, sig)
        m.d.comb += Assert(u.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(u.rd == Const(0b10000, 5))
        m.d.comb += Assert(u.imm == Const(0b00100010000110111111000000000000, 32))

    def verify_jtype(self, m):
        sig = self.build_signal(m, "U", [(0,6,"1001011"), (7,11, "10000"), 
            (12,19,"00100010"),
            (20,20,"1"),
            (21,30,"1011000111"),
            (31,31,"1")])

        j = JType("jtype")
        j.elaborate(m.d.comb, sig)
        m.d.comb += Assert(j.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(j.rd == Const(0b10000, 5))
        m.d.comb += Assert(j.imm == Const(0b100100010110110001110, 32))

    def main(self):
        m = Module()
        ports=[]
        self.verify_rtype(m)
        ports += self.verify_itype(m)
        self.verify_stype(m)
        self.verify_btype(m)
        self.verify_utype(m)
        self.verify_jtype(m)


        parser = main_parser()
        args = parser.parse_args()
        main_runner(parser, args, m, ports=ports)
    
    

    

if __name__ == "__main__":
    __Verify().main()
