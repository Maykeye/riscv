from nmigen import Module, Value
from nmigen.asserts import Assert, Past
from core import Core
from register_file import RegisterFile
from typing import Optional, List
from encoding import IType
from skeleton import SeqPast

class VerificationRegisterFile:
    def capture(self, m:Core, core:Core, past:int):
        comb = m.d.comb
        if past > 0:
            prefix=f"past{past}"
        else:
            prefix="sample"
        self.r = RegisterFile(core.xlen, prefix=prefix)
        for i in range(self.r.main_gpr_count()):
            comb += self.r[i].eq(Past(core.r[i], past))
        comb += self.r.pc.eq(Past(core.r.pc, past))

        # TODO: move to additional structure
        self.itype = IType(prefix=f"{prefix}_i")
        self.itype.elaborate(comb, Past(core.input_data[0], past))
        self.input_ready = Signal.like(core.input_ready, name=f"{prefix}_input_ready")
        comb += self.input_ready.eq(Past(core.input_ready, past))
        

    
    def assert_same_gpr_but_one(self, m:Core, other:RegisterFile, skip:Value):        
        comb = m.d.comb

        for i in range(self.r.main_gpr_count()):
            with m.If(skip != i):
                comb += Assert(self.r[i] == other[i])

    def assert_pc_advanced(self, m:Core, previous:RegisterFile):
        comb = m.d.comb
        comb += Assert(self.r.pc == (previous.r.pc + 4)[:self.r.pc.width])


class ProofOverTicks:
    def __init__(self, ticks:int):
        self.ticks = ticks 
        self.time : List[VerificationRegisterFile] = [] #n-th element corresponts to state n ticks backs
        self.uut : Optional[Core] = None
        self.module : Optional[Core] = None

    def run(self, m : Core, uut : Core):
        self.uut = uut
        self.module = m
        for i in range(self.ticks+1):
            regs = VerificationRegisterFile()
            regs.capture(m, uut, i)
            self.time.append(regs)

        for i in range(self.ticks):
            self.run_tick_proof(i)

        no_resets = Const(1, 1)

        for expect in [True, False]:
            locked_pins = self.signals_expectation(uut, expect)        
            for locked_pin in locked_pins:
                no_resets = no_resets & SeqPast(locked_pin, self.ticks, 0, expect)

        with m.If(no_resets):
            self.run_main_proof()

        self.run_proof_no_aux_signals()
    
    def run_main_proof(self):
        pass

    def run_proof_no_aux_signals(self):
        """ Proof that is run without checking for any signals in sequences from signals_expectation(x) """
        pass

    def signals_expectation(self, uut, expect):
        """ return pins that must have state=expect during all ticks
        e.g. for reset on positive, signals_expectation(uut, False)=[rst_p] as reset must be low """
        return []
        



    def run_tick_proof(self, steps_back : int):
        """ Utility function for proofs that might require different proves over different times """
        pass

from nmigen import Const, Signal
from opcodes import Opcode, OpImm
class ProofAdd(ProofOverTicks): 
    def __init__(self):
        super().__init__(1)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset]
        return []

    def run_main_proof(self):        
        m = self.module
        core : Core = self.uut
        comb = m.d.comb

        last = self.time[1]
        now = self.time[0]

        # General proof
        with m.If(last.itype.match(opcode=Opcode.OpImm, funct3=OpImm.ADD) & last.input_ready):
            with m.If(last.itype.rd == 0):
                comb += Assert(now.r[0] == 0)
            with m.Else():
                addi_expecetd = Signal(core.xlen)
                comb += addi_expecetd.eq(last.r[last.itype.rs1] + last.itype.imm)
                comb += Assert(addi_expecetd == now.r[last.itype.rd])

            now.assert_pc_advanced(m, last)                
            now.assert_same_gpr_but_one(m, last.r, last.itype.rd)
                


        