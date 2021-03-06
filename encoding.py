from typing import List
from nmigen import Signal, Cat, Const, Value, Repl
from nmigen.hdl.ast import Statement

# for verification
from nmigen import Module
from nmigen.asserts import Assert, Assume
from nmigen.cli import main_parser, main_runner

from skeleton import bit_slice

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
        comb += self.imm.eq(Cat(input[20:32], Repl(input[31], 20)))
        

    def match(self, opcode=None, rd=None, funct3=None, rs1=None, imm=None) -> Value:
        """ Build boolean expression that matches x against provided parts """
        if type(imm) == int:
            assert imm.bit_length() <= 32, "imm must be 32 bit long(12 bits+signext)"
            imm = imm & (2**32)-1
        subexpressions = []
        if opcode is not None: subexpressions.append(self.opcode.matches(opcode))
        if rd is not None: subexpressions.append(self.rd.matches(rd))
        if funct3 is not None: subexpressions.append(self.funct3.matches(funct3))
        if rs1 is not None: subexpressions.append(self.rs1.matches(rs1))
        if imm is not None: subexpressions.append(self.imm.matches(imm))

        if not subexpressions:
            print("warning: no matches provided for itype.match")
            return Const(1)
        res = subexpressions.pop(0)
        while subexpressions:
            res = res & subexpressions.pop(0)
        return res


    @staticmethod
    def build_i32(opcode:int=0, rd:int=0, funct3:int=0,rs1:int=0, imm:int=0, ensure_ints=True)->int:        
        if type(imm) == int:
            assert -2**12 <= imm < 2**12
        imm = imm & ((2**12)-1)

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
    
    @staticmethod
    def build_i32(opcode:int=0, rd:int=0, imm:int=0)->int:        
        if type(imm) == int:
            assert imm.bit_length() <= 32, "imm must be 32 bit long(12 bits+signext)"
            assert imm & ((1<<12)-1) == 0, "lower 12 bits must be zero"
        imm = imm & 0xFFFFFFFF

        word = (opcode) | (rd << 7) | (bit_slice(imm, 31, 12) << 12) 
        return word

    def match(self, opcode=None, rd=None, imm=None) -> Value:
        """ Build boolean expression that matches x against provided parts """
        if type(imm) == int:
            assert imm.bit_length() <= 32, "imm must be 32 bit long(12 bits+signext)"
            assert imm & ((1<<12)-1) == 0, "lower 12 bits must be zero"
            imm = imm & (2**32)-1
        subexpressions = []
        if opcode is not None: subexpressions.append(self.opcode.matches(opcode))
        if rd is not None: subexpressions.append(self.rd.matches(rd))
        if imm is not None: subexpressions.append(self.imm.matches(imm))

        if not subexpressions:
            print("warning: no matches provided for utype.match")
            return Const(1)
        res = subexpressions.pop(0)
        while subexpressions:
            res = res & subexpressions.pop(0)
        return res

       
class BType:
    def __init__(self, prefix=""):
        if prefix:
            prefix+="_"
        self.opcode = Signal(7,name=f"{prefix}opcode")
        self.funct3 = Signal(3,name=f"{prefix}funct3")
        self.rs1 = Signal(5,name=f"{prefix}rs1")
        self.rs2 = Signal(5,name=f"{prefix}rs2")
        self.imm = Signal(32,name=f"{prefix}imm")

    def elaborate(self, comb:List[Statement], input:Signal):
        comb += self.opcode.eq(input[0:7])
        comb += self.funct3.eq(input[12:15])
        comb += self.rs1.eq(input[15:20])
        comb += self.rs2.eq(input[20:25])
        comb += self.imm.eq(Cat(Const(0,1), input[8:12], input[25:31], input[7], Repl(input[31], 20)))

    @staticmethod
    def build_i32(opcode, funct3, rs1, rs2, imm):
        if type(imm) == int:
            assert imm % 2 == 0
            assert imm.bit_length() <= 32, "imm must be 32 bit long"
            imm = imm & (2**32)-1
        value = opcode
        value = value | (funct3 << 12) 
        value = value | (rs1 << 15) 
        value = value | (rs2 << 20) 
        value = value | ((bit_slice(imm, 4, 1)) << 8)
        value = value | ((bit_slice(imm, 10, 5)) << 25)
        value = value | ((bit_slice(imm, 11, 11)) << 7)
        value = value | ((bit_slice(imm, 12, 12)) << 31)

        return value


    def match(self, opcode=None, funct3=None, rs1=None, rs2=None, imm=None) -> Value:
        """ Build boolean expression that matches x against provided parts """
        if type(imm) == int:
            # TOOD: other types need it as well
            assert imm.bit_length() <= 32, "imm must be 32 bit long"
            assert imm % 2 == 0, "btype has 2-byte offset"
            # TODO: check ~20 hi bits of imm == sigen ext
            imm = imm & (2**32)-1
        subexpressions = []
        if opcode is not None: subexpressions.append(self.opcode.matches(opcode))
        if funct3 is not None: subexpressions.append(self.funct3.matches(funct3))
        if rs1 is not None: subexpressions.append(self.rs1.matches(rs1))
        if rs2 is not None: subexpressions.append(self.rs2.matches(rs2))
        if imm is not None: subexpressions.append(self.imm.matches(imm))

        if not subexpressions:
            print("warning: no matches provided for btype.match")
            return Const(1)
        res = subexpressions.pop(0)
        while subexpressions:
            res = res & subexpressions.pop(0)
        return res

        

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
        comb += self.imm.eq(Cat(Const(0, 1), input[21:31], input[20], input[12:20], Repl(input[31], 12)))
    
    def match(self, opcode=None, rd=None, imm=None) -> Value:
        """ Build boolean expression that matches x against provided parts """
        if type(imm) == int:
            assert imm.bit_length() <= 32, "imm must be 32 bit long(12 bits+signext)"
            assert imm % 2 == 0, "jtype has 2-byte offset"
            imm = imm & (2**32)-1
        subexpressions = []
        if opcode is not None: subexpressions.append(self.opcode.matches(opcode))
        if rd is not None: subexpressions.append(self.rd.matches(rd))
        if imm is not None: subexpressions.append(self.imm.matches(imm))

        if not subexpressions:
            print("warning: no matches provided for jtype.match")
            return Const(1)
        res = subexpressions.pop(0)
        while subexpressions:
            res = res & subexpressions.pop(0)
        return res

    @staticmethod
    def build_i32(opcode:int=0, rd:int=0, imm:int=0)->int:        
        if type(imm) == int:
            assert -2**21 <= imm < 2**21
            assert imm % 2 == 0
        imm = imm & ((2**21)-1)

        word = (opcode) | (rd << 7) | (bit_slice(imm, 10, 1) << 21) | (bit_slice(imm,11,11) << 20) | (bit_slice(imm, 19,12) << 12) 
        word = word | (bit_slice(imm,20,20) << 31)
        return word



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
        return []

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


        # matcher
        m.d.comb += Assert(i.match(opcode=0b1001011))
        m.d.comb += Assert(i.match(rd=0b10000))
        m.d.comb += Assert(i.match(funct3=1))
        m.d.comb += Assert(i.match(rs1=2))
        m.d.comb += Assert(i.match(imm=0b11111111111111111111100110111111))
        
        # builder
        i_builder_check = Signal(32)
        i_builder_opcode = Signal(7)
        i_builder_rd = Signal(5)
        i_builder_funct3 = Signal(3)
        i_builder_rs1 = Signal(5)
        i_builder_imm = Signal(11)


        built_itype = IType.build_i32(i_builder_opcode, i_builder_rd, i_builder_funct3, i_builder_rs1, i_builder_imm, ensure_ints=False)
        m.d.comb += i_builder_check.eq(built_itype)
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
        return []

    def verify_btype(self, m):
        sig = self.build_signal(m, "B", [(0,6,"1001011"), (7,7, "1"), (8,11,"0000"), (12,14,"001"), (15, 19, "00010"), (20,24,"00011"), 
            (25,30, "011111"), (31,31,"1")])
        b = BType("btype")
        b.elaborate(m.d.comb, sig)
        m.d.comb += Assert(b.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(b.funct3 == Const(1, 3))
        m.d.comb += Assert(b.rs1 == Const(2, 5))
        m.d.comb += Assert(b.rs2 == Const(3, 5))
        m.d.comb += Assert(b.imm == Cat(Const(0b1101111100000, 13), Repl(1, 19)))

        m.d.comb += Assert(b.match(opcode=0b1001011))
        m.d.comb += Assert(b.match(rs1=2))
        m.d.comb += Assert(b.match(rs2=3))        
        m.d.comb += Assert(b.match(funct3=1))
        m.d.comb += Assert(b.match(imm=0b11111111111111111111101111100000))
        m.d.comb += Assert(b.match(opcode=0b1001011, funct3=1, rs1=2, rs2=3, imm=0b11111111111111111111101111100000))
        m.d.comb += Assert(~b.match(opcode=0b1001011, funct3=3, rs1=1, rs2=5, imm=0b11111111111111111111101111100000))


        b_builder_check = Signal(32)
        b_builder_opcode = Signal(7)
        b_builder_f3 = Signal(3)
        b_builder_rs1 = Signal(5)
        b_builder_rs2 = Signal(5)
        b_builder_imm = Signal(13)
        m.d.comb += Assume(b_builder_imm[0] == 0)

        built_btype = BType.build_i32(opcode = b_builder_opcode, funct3=b_builder_f3, rs1=b_builder_rs1, rs2=b_builder_rs2, imm=b_builder_imm)
        m.d.comb += b_builder_check.eq(built_btype)
        b = BType("btype.build")
        b.elaborate(m.d.comb, built_btype)
        m.d.comb += Assert(b_builder_opcode == b.opcode)        
        m.d.comb += Assert(b_builder_imm == Cat(Const(0,1), b.imm[1:13]))
        m.d.comb += Assert(b.imm[13:32] == Repl(b_builder_imm[12], 32-13))

        return [b_builder_check, b_builder_opcode, b_builder_f3, b_builder_rs1, b_builder_rs2, b_builder_imm]

     
    def verify_utype(self, m):        
        sig = self.build_signal(m, "U", [(0,6,"1001011"), (7,11, "10000"), (12,31,"00100010000110111111")])
        u = UType("utype")
        u.elaborate(m.d.comb, sig)
        m.d.comb += Assert(u.opcode == Const(0b1001011, 7))
        m.d.comb += Assert(u.rd == Const(0b10000, 5))
        m.d.comb += Assert(u.imm == Const(0b00100010000110111111000000000000, 32))

        m.d.comb += Assert(u.match(opcode=0b1001011))
        m.d.comb += Assert(u.match(rd=0b10000))
        m.d.comb += Assert(u.match(imm=0b00100010000110111111000000000000))

        m.d.comb += Assert(u.match(opcode=0b1011011)==0)
        m.d.comb += Assert(u.match(rd=0b11000)==0)
        m.d.comb += Assert(u.match(imm=0b10100010000110111111000000000000)==0)

        m.d.comb += Assert(u.match(opcode=0b1001011, rd=0b10000, imm=0b00100010000110111111000000000000))


        u = UType("utype.sign")
        u.elaborate(m.d.comb, Const(0x8000_0000, 32))
        m.d.comb += Assert(u.imm[31] == 1)

        u = UType("utype.trailzero")
        u.elaborate(m.d.comb, Const(0xFFFF_FFFF, 32))
        m.d.comb += Assert(u.imm.bit_select(0,12) == 0)
        
        u_builder_check = Signal(32)
        u_builder_opcode = Signal(7)
        u_builder_rd = Signal(5)
        u_builder_imm = Signal(20)
        m.d.comb += Assume(u_builder_imm[0:12] == 0)

        built_utype = UType.build_i32(opcode=u_builder_opcode, rd=u_builder_rd, imm=u_builder_imm)
        m.d.comb += u_builder_check.eq(built_utype)
        u = UType("utype.build")        
        u.elaborate(m.d.comb, built_utype)
        m.d.comb += Assert(u_builder_opcode == u.opcode)
        m.d.comb += Assert(u_builder_rd == u.rd)
        m.d.comb += Assert(Cat(Repl(0, 12), u_builder_imm[12:32]) == u.imm)

        
        return [u_builder_check, u_builder_opcode, u_builder_rd, u_builder_imm]

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
        m.d.comb += Assert(j.imm == Const(0b1111_1111_1111_0010_0010_1101_1000_1110, 32))

        m.d.comb += Assert(j.match(opcode=0b1001011))
        m.d.comb += Assert(j.match(opcode=0b1001010)==0)
        m.d.comb += Assert(j.match(rd=0b10000))
        m.d.comb += Assert(j.match(rd=0b00001)==0)
        m.d.comb += Assert(j.match(imm=0b1111_1111_1111_0010_0010_1101_1000_1110)) #extra bits - sign ext
                                         
        m.d.comb += Assert(j.match(imm=0b110100010110110001110)==0)
        m.d.comb += Assert(j.match(opcode=0b1001011, rd=0b10000, imm=0b1111_1111_1111_0010_0010_1101_1000_1110))


        j_builder_check = Signal(32)
        j_builder_opcode = Signal(7)
        j_builder_rd = Signal(5)
        j_builder_imm = Signal(21)
        m.d.comb += Assume(j_builder_imm[0] == 0)

        built_jtype = JType.build_i32(opcode=j_builder_opcode, rd=j_builder_rd, imm=j_builder_imm)
        m.d.comb += j_builder_check.eq(built_jtype)
        j = JType("jtype.build")
        j.elaborate(m.d.comb, built_jtype)
        m.d.comb += Assert(j_builder_opcode == j.opcode)
        m.d.comb += Assert(j_builder_rd == j.rd)
        m.d.comb += Assert(j_builder_imm == j.imm[0:21])


        j = JType("jtype.se")
        j.elaborate(m.d.comb, Const(0x8000_0000, 32))
        m.d.comb += Assert(j.imm[20] == 1)
        m.d.comb += Assert(j.imm[31] == 1)

        j = JType("jtype.ze")
        j.elaborate(m.d.comb, Const(0x7FFF_FFFF, 32))
        m.d.comb += Assert(j.imm[20] == 0)
        m.d.comb += Assert(j.imm[31] == 0)

        return [j_builder_check, j_builder_opcode, j_builder_rd, j_builder_imm]


    def main(self):
        m = Module()
        ports=[]
        ports += self.verify_rtype(m)
        ports += self.verify_itype(m)
        ports += self.verify_stype(m)
        ports += self.verify_btype(m)
        ports += self.verify_utype(m)
        ports += self.verify_jtype(m)


        parser = main_parser()
        args = parser.parse_args()
        main_runner(parser, args, m, ports=ports)
    
    


if __name__ == "__main__":
    __Verify().main()
