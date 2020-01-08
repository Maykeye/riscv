from nmigen import Module, Value, Signal, Const, Array
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
        self.input_data = Array([Signal(core.xlen, name=f"{prefix}_input_{i}") for i in range(core.look_ahead)])
        
        self.cycle = Signal.like(core.cycle, name=f"{prefix}_cycle")
        comb += self.cycle.eq(Past(core.cycle, past))

        # TODO: move to structure
        self.mem2core_addr = Signal.like(core.mem2core_addr, name=f"{prefix}_mem2core_addr")
        self.mem2core_en = Signal.like(core.mem2core_en, name=f"{prefix}_mem2core_en")
        self.mem2core_seq = Signal.like(core.mem2core_seq, name=f"{prefix}_mem2core_seq")
        comb += self.mem2core_addr.eq(Past(core.mem2core_addr, past))
        comb += self.mem2core_en.eq(Past(core.mem2core_en, past))
        comb += self.mem2core_seq.eq(Past(core.mem2core_seq, past))




        comb += self.input_ready.eq(Past(core.input_ready, past))
        for i in range(core.look_ahead):
            comb += self.input_data[i].eq(Past(core.input_data[i], past))

    def assert_loading_from (self, m:Core, addr, src_loc_at=1):
        comb = m.d.comb
        comb += Assert(self.mem2core_en, src_loc_at=src_loc_at)
        comb += Assert(self.mem2core_addr == addr, src_loc_at=src_loc_at)

    def assert_same_gpr(self, m:Core, other:RegisterFile, src_loc_at=1):
        comb = m.d.comb

        for i in range(self.r.main_gpr_count()):
            comb += Assert(self.r[i] == other[i], src_loc_at=src_loc_at)

    
    def assert_same_gpr_but_one(self, m:Module, other:RegisterFile, skip:Value, src_loc_at=1):
        comb = m.d.comb

        for i in range(self.r.main_gpr_count()):
            with m.If(skip != i):
                comb += Assert(self.r[i] == other[i], src_loc_at=src_loc_at)

    def assert_gpr_value(self, m:Module, idx:Value, expected_value:Value, src_loc_at=1):
        """ Assert GPR value (ignored for idx = 0 and zeri is checked instead) """
        comb = m.d.comb
        with m.If(idx == 0):
            comb += Assert(self.r[0] == 0, src_loc_at=src_loc_at)
        with m.Else():
            comb += Assert(self.r[idx] == expected_value, src_loc_at=src_loc_at)


    def assert_pc_advanced(self, m:Module, previous:RegisterFile, src_loc_at=1):
        comb = m.d.comb
        comb += Assert(self.r.pc == (previous.pc + 4)[:self.r.pc.width], src_loc_at=src_loc_at)

    def assert_same_pc(self, m:Module, previous:RegisterFile, src_loc_at=1):        
        comb = m.d.comb
        comb += Assert(self.r.pc == previous.pc, src_loc_at=src_loc_at)

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