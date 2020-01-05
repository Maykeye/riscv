from enum import IntEnum, auto

class Opcode(IntEnum):
    OpImm = 0b0010011
    Jal   = 0b1101111

class OpImm(IntEnum):
    ADD  = 0b000,
    SHIFT_LEFT  = 0b001,
    SLT  = 0b010,
    SLTU = 0b011,
    XOR  = 0b100,
    OR   = 0b110,
    AND  = 0b111,
    SHIFT_RIGHT = 0b101


class OpAlu(IntEnum):
    """ Bitwise identical to OpImm"""
    ADD  = 0b000,
    SLT  = 0b010,
    SLTU = 0b011,
    XOR  = 0b100,
    OR   = 0b110,
    AND  = 0b111,


class DebugOpcode(IntEnum):
    NOP=auto()
    INVALID=auto()
    AWAIT_READ=auto()
    IN_RESET=auto()
    NOT_SPECIFIED=auto()
    ADD_imm  = auto()
    SLL_imm  = auto()
    SLT_imm  = auto()
    SLTIU_imm = auto()
    XOR_imm  = auto()
    OR_imm   = auto()
    AND_imm  = auto()
    SRA_imm = auto()
    SRL_imm = auto()
    JAL=auto()

    UNREACHABLE = auto()
