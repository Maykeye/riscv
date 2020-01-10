from nmigen import Const, Signal, ResetSignal, signed, Module, Value, Repl
from nmigen.asserts import Assert
from opcodes import Opcode, OpLoad
from proofs.verification import ProofOverTicks
from core import Core
from typing import List
from membuild import MemBuild

class ProofLoadBase(ProofOverTicks): 
    MAX_DELAY=5   

    def match(self, rv:Value, input:Value) -> Value:
        """ Return true if value in rv matches to what was in input """
        raise NotImplementedError()

    def op_load(self) -> OpLoad:
        raise NotImplementedError()

    def __init__(self):
        super().__init__(ProofLoadBase.MAX_DELAY)

    def signals_expectation(self, uut : Core, expect : bool) -> List[Signal]:
        if expect == False:
            return [uut.in_reset, uut.clock.rst]
        return []

    def run_main_proof(self):        
        first = self.time[ProofLoadBase.MAX_DELAY]
        m : Module = self.module
        comb = m.d.comb

        with m.If(first.at_instruction_start() & first.itype.match(opcode=Opcode.Load, funct3=self.op_load())):
            check_only = None
            #check_only = 3

            source_address = (first.r[first.itype.rs1] + first.itype.imm)[:32]

            for i in range(ProofLoadBase.MAX_DELAY-1, 0,-1):
                if check_only is not None and i != check_only:
                    continue
                now = self.time[i]
                next = self.time[i-1]
                
                with m.If(self.previously_no_data_arrived(i)):                    
                    now.assert_loading_from(m, source_address)
                    now.assert_same_gpr(m, first.r)                    
                    now.assert_same_pc(m, first.r)
                    with m.If(~now.input_ready):
                        pass
                    with m.Else():
                        next.assert_same_gpr_but_one(m, first.r, first.itype.rd)
                        next.assert_pc_advanced(m, now.r)
                        with m.If(first.itype.rd == 0):
                            comb += Assert(next.r[0] == 0)
                        with m.Else():
                            self.match(next.r[first.itype.rd], now.input_data[0])
                        
                
    def previously_no_data_arrived(self, currenct_time):
        """ Build an expression to check that no data arrivied from memory unit from FIRST+1 state until CURRENT-1 state """
        term = Const(1,1)
        for i in range(ProofLoadBase.MAX_DELAY-1, currenct_time, -1):
            term = term & (~self.time[i].input_ready[0])
        return term
                

class ProofLB(ProofLoadBase):
    def op_load(self):
        return OpLoad.LB
    
    def match(self, rv, input):
        m : Module = self.module
        comb = m.d.comb
        comb += Assert(rv[0:8] == input[0:8])
        with m.If(input[7]):
            comb += Assert(rv[8:32] == -1)
        with m.Else():
            comb += Assert(rv[8:32] == 0)
        
    def simulate(self):
        return (MemBuild() 
            .set_origin(0x100)
            .add_i32(0x12345678)
            .add_i32(0xF0E0B0C0)
            .set_origin(0x200)
            .lb(1, 0, 0x100)
            .lb(2, 0, 0x104)
            .lb(3, 0, 0x101)
            .nop()
        ).dict

class ProofLBU(ProofLoadBase):
    def op_load(self):
        return OpLoad.LBU
    
    def match(self, rv, input):
        m : Module = self.module
        comb = m.d.comb
        comb += Assert(rv[0:8] == input[0:8])
        comb += Assert(rv[8:32] == 0)
        
    def simulate(self):
        return (MemBuild() 
            .set_origin(0x100)
            .add_i32(0x12345678)
            .add_i32(0xF0E0B0C0)
            .set_origin(0x200)
            .lbu(1, 0, 0x100)
            .lbu(2, 0, 0x104)
            .lbu(3, 0, 0x101)
            .nop()
        ).dict

class ProofLH(ProofLoadBase):
    def op_load(self):
        return OpLoad.LH
    
    def match(self, rv, input):
        m : Module = self.module
        comb = m.d.comb
        comb += Assert(rv[0:16] == input[0:16])
        with m.If(input[15]):
            comb += Assert(rv[16:32] == -1)
        with m.Else():
            comb += Assert(rv[16:32] == 0)
        
    def simulate(self):
        return (MemBuild() 
            .set_origin(0x100)
            .add_i32(0x12345678)
            .add_i32(0xF0E0B0C0)
            .set_origin(0x200)
            .lh(1, 0, 0x100)
            .lh(2, 0, 0x104)
            .lh(3, 0, 0x101)
            .nop()
        ).dict

class ProofLHU(ProofLoadBase):
    def op_load(self):
        return OpLoad.LHU
    
    def match(self, rv, input):
        m : Module = self.module
        comb = m.d.comb
        comb += Assert(rv[0:16] == input[0:16])
        comb += Assert(rv[16:32] == 0)
        
    def simulate(self):
        return (MemBuild() 
            .set_origin(0x100)
            .add_i32(0x12345678)
            .add_i32(0xF0E0B0C0)
            .set_origin(0x200)
            .lhu(1, 0, 0x100)
            .lhu(2, 0, 0x104)
            .lhu(3, 0, 0x101)
            .nop()
        ).dict

class ProofLW(ProofLoadBase):
    def op_load(self):
        return OpLoad.LW
    
    def match(self, rv, input):
        m : Module = self.module
        comb = m.d.comb
        comb += Assert(rv[0:32] == input)
        #TODO: sext for 64 mode
        
    def simulate(self):
        return (MemBuild() 
            .set_origin(0x100)
            .add_i32(0x12345678)
            .add_i32(0xF0E0B0C0)
            .set_origin(0x200)
            .lw(1, 0, 0x100)
            .lw(2, 0, 0x104)
            .lw(3, 0, 0x101)
            .nop()
        ).dict


