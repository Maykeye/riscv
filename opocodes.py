from enum import IntEnum, auto

class Opcode(IntEnum):
    OpImm = 0b0010011

class OpImm(IntEnum):
    ADDI  = 0b000,
    SHIFT_LEFT  = 0b001,
    SLTI  = 0b010,
    SLTIU = 0b011,
    XORI  = 0b100,
    ORI   = 0b110,
    ANDI  = 0b111,
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