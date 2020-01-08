from nmigen import Module, Signal, Mux, Const, Value, Cat, Repl

from instruction import Instruction
from core import Core
from opcodes import Opcode, DebugOpcode, OpLoad
from proofs.load import ProofLB


class LoadBase(Instruction):
    def funct3(self):
        raise NotImplementedError()
    def debug_opcode(self):
        raise NotImplementedError()
    def process_load(self, data) -> Value:
        raise NotImplementedError()
    
    def check(self):
        """ Check that instruction can be executed """
        core : Core = self.core
        return (core.itype.opcode == Opcode.Load) & (core.itype.funct3 == self.funct3())


    def implement(self):            
        core : Core = self.core
        iclk = core.iclk
        m = core.current_module

        read_address = (core.query_rs1() + core.itype.imm)[:32]
        core.emit_debug_opcode(self.debug_opcode(), read_address)

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
                
            




class LbInstr(LoadBase):
    def funct3(self):
        return OpLoad.LB

    def process_load(self, input_value):
        lb_value = Signal(32)
        comb = self.core.current_module.d.comb
        comb += lb_value.eq(Cat(input_value[0:8], Repl(input_value[7], 24)))
        return lb_value

    def debug_opcode(self):
        return DebugOpcode.LB

    def proofs(self):
        return [ProofLB]