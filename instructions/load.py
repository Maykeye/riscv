from nmigen import Module, Signal, Mux, Const, Value, Cat, Repl

from instruction import Instruction
from core import Core
from opcodes import Opcode, DebugOpcode, OpLoad
from proofs.load import ProofLB, ProofLBU, ProofLH, ProofLHU, ProofLW

class LoadBase(Instruction):
    def funct3(self):
        raise NotImplementedError()
    def debug_opcodes(self):
        raise NotImplementedError()
    def process_load(self, data) -> Value:
        raise NotImplementedError()
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return (core.itype.opcode == Opcode.Load) & (core.itype.funct3[0:2] == (self.funct3() & 0b11) )


    def implement(self):            
        core : Core = self.core
        iclk = core.iclk
        m = core.current_module

        read_address = (core.query_rs1() + core.itype.imm)[:32]
        debug_opcode = Mux(core.itype.funct3[2], self.debug_opcodes()[1], self.debug_opcodes()[0])
        core.emit_debug_opcode(debug_opcode, read_address)

        #core.process_cycle(0)
        with m.If(core.cycle == 0):
            core.schedule_read(read_address, 0)
            iclk += core.cycle.eq(1)

        #core.process_cycle(1, advance_cycle=False)
        with m.Elif(core.cycle == 1):
            with m.If(core.input_ready[0]):
                value = self.process_load(core.input_data[0])
                core.assign_gpr(core.itype.rd, value)                
                core.move_pc_to_next_instr()
            with m.Else():
                core.emit_debug_opcode(DebugOpcode.AWAIT_READ, read_address)
                
            




class LbLbuInstr(LoadBase):
    def funct3(self):
        return OpLoad.LB

    def process_load(self, input_value):
        lb_value = Signal(32)
        comb = self.core.current_module.d.comb
        
        bit_to_replicate=Mux(self.core.itype.funct3[2], Const(0,1), input_value[7])
        comb += lb_value.eq(Cat(input_value[0:8], Repl(bit_to_replicate, 24)))
        return lb_value

    def debug_opcodes(self):
        return [DebugOpcode.LB, DebugOpcode.LBU]

    def proofs(self):
        return [ProofLB, ProofLBU]


class LhLhuInstr(LoadBase):
    def funct3(self):
        return OpLoad.LH

    def process_load(self, input_value):
        lh_value = Signal(32)
        comb = self.core.current_module.d.comb
        
        bit_to_replicate=Mux(self.core.itype.funct3[2], Const(0,1), input_value[15])
        comb += lh_value.eq(Cat(input_value[0:16], Repl(bit_to_replicate, 16)))
        return lh_value

    def debug_opcodes(self):
        return [DebugOpcode.LH, DebugOpcode.LHU]

    def proofs(self):
        return [ProofLH, ProofLHU]

class LwInstr(LoadBase):
    def funct3(self):
        return OpLoad.LW

    def process_load(self, input_value):
        lw_value = Signal(32)
        comb = self.core.current_module.d.comb
        # TODO: report "unsigned" lw as error instruction
        comb += lw_value.eq(input_value)
        return lw_value

    def debug_opcodes(self):
        return [DebugOpcode.LW, DebugOpcode.LW]

    def proofs(self):
        return [ProofLW]

