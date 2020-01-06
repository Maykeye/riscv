from nmigen import Module, Value, Signal, Const
from nmigen.asserts import Assert, Past
from core import Core
from register_file import RegisterFile
from typing import Optional, List
from encoding import IType, JType, UType, BType
from skeleton import SeqPast

class VerificationRegisterFile:
    def capture(self, m:Core, core:Core, past:int):
        comb = m.d.comb
        if past > 0:
            prefix=f"past{past}"
        else:
            prefix="now"
        self.r = RegisterFile(core.xlen, prefix=prefix)
        for i in range(self.r.main_gpr_count()):
            comb += self.r[i].eq(Past(core.r[i], past))
        comb += self.r.pc.eq(Past(core.r.pc, past))

        # TODO: move to additional structure
        self.itype = IType(prefix=f"{prefix}_i")        
        self.itype.elaborate(comb, Past(core.input_data[0], past))

        self.jtype = JType(prefix=f"{prefix}_j")
        self.jtype.elaborate(comb, Past(core.input_data[0], past))

        self.utype = UType(prefix=f"{prefix}_u")
        self.utype.elaborate(comb, Past(core.input_data[0], past))

        self.btype = BType(prefix=f"{prefix}_b")
        self.btype.elaborate(comb, Past(core.input_data[0], past))

        self.input_ready = Signal.like(core.input_ready, name=f"{prefix}_input_ready")        
        comb += self.input_ready.eq(Past(core.input_ready, past))
        
    def assert_same_gpr(self, m:Core, other:RegisterFile, src_loc_at=1):
        comb = m.d.comb

        for i in range(self.r.main_gpr_count()):
            comb += Assert(self.r[i] == other[i], src_loc_at=src_loc_at)

    
    def assert_same_gpr_but_one(self, m:Core, other:RegisterFile, skip:Value, src_loc_at=1):
        comb = m.d.comb

        for i in range(self.r.main_gpr_count()):
            with m.If(skip != i):
                comb += Assert(self.r[i] == other[i], src_loc_at=src_loc_at)

    def assert_pc_advanced(self, m:Module, previous:RegisterFile, src_loc_at=1):
        #TODO: previous is not a RF
        comb = m.d.comb
        comb += Assert(self.r.pc == (previous.r.pc + 4)[:self.r.pc.width], src_loc_at=src_loc_at)


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

    def simulate(self):
        """ Run simulation. If proof doesn't has special simulation demo, instruction.simulation() will be called"""
        raise Exception("Must be implemented in child class")