from enum import Enum
from classes.errors import InvalidOpcode


class Type(Enum):
    """
    Holds all MIPS instruction types.
    """
    R = "R"
    I = "I"
    J = "J"


class Opcode():
    """
    Opcode class for decoding instruction names.
    """
    opcode = None
    function = None

    decoder = {
        (35, None) : ("lw",   Type.I),
        (43, None) : ("sw",   Type.I),
        (0, 32)    : ("add",  Type.R),
        (8, None)  : ("addi", Type.I),
        (0, 34)    : ("sub",  Type.R),
        (0, 36)    : ("and",  Type.R),
        (12, None) : ("andi", Type.I),
        (0, 37)    : ("or",   Type.R),
        (13, None) : ("ori",  Type.I),
        (0, 38)    : ("xor",  Type.R),
        (14, None) : ("xori", Type.I),
        (0, 39)    : ("nor",  Type.R),
        (0, 42)    : ("slt",  Type.R),
        (10, None) : ("slti", Type.I),
        (15, None) : ("lui",  Type.I),
        (0, 0)     : ("sll",  Type.R),
        (0, 3)     : ("sra",  Type.R),
        (0, 24)    : ("mult", Type.R),
        (0, 26)    : ("div",  Type.R),
        (6, None)  : ("blez", Type.I),
        (7, None)  : ("bgtz", Type.I),
        (4, None)  : ("beq",  Type.I),
        (5, None)  : ("bne",  Type.I),
        (2, None)  : ("j",    Type.J),
        (3, None)  : ("jal",  Type.J),
        (0, 8)     : ("jr",   Type.R),
        (0, 16)    : ("mfhi", Type.R),
        (0, 18)    : ("mflo", Type.R)
    }

    def __init__(self, opcode, function):
        """
        Opcode class constructor
        :param name: incoming instruction name to decode to opcode.
        """
        self.opcode = opcode
        self.function = function


    def decode(self):
        """
        Decode the stored instruction name into its opcode integer part.
        :return: Integer representation of opcode.
        """
        try:
            return self.decoder[self.opcode, self.function]
        except KeyError:
            raise InvalidOpcode((self.opcode, self.function))