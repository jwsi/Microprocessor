from classes.errors import InvalidInstructionName
from enum import Enum


class Type(Enum):
    """
    Holds all MIPS instruction types.
    """
    R = "R"
    I = "I"
    J = "J"


class Opcode():
    """
    Opcode class for decoding assembly instruction names.
    """
    name = None
    # Decoder is of form (type, opcode, function)
    decoder = {
        "lw"   : (Type.I, 35, None),
        "sw"   : (Type.I, 43, None),
        "add"  : (Type.R,  0, 32  ),
        "addi" : (Type.I,  8, None),
        "sub"  : (Type.R,  0, 34  ),
        "and"  : (Type.R,  0, 36  ),
        "andi" : (Type.I, 12, None),
        "or"   : (Type.R,  0, 37  ),
        "ori"  : (Type.I, 13, None),
        "xor"  : (Type.R,  0, 38  ),
        "xori" : (Type.I, 14, None),
        "nor"  : (Type.R,  0, 39  ),
        "slt"  : (Type.R,  0, 42  ),
        "slti" : (Type.I, 10, None),
        "lui"  : (Type.I, 15, None),
        "sll"  : (Type.R,  0,  0  ),
        "sra"  : (Type.R,  0,  3  ),
        "mult" : (Type.R,  0, 24  ),
        "div"  : (Type.R,  0, 26  ),
        "blez" : (Type.I,  6, None),
        "bgtz" : (Type.I,  7, None),
        "beq"  : (Type.I,  4, None),
        "bne"  : (Type.I,  5, None),
        "j"    : (Type.J,  2, None),
        "jal"  : (Type.J,  3, None),
        "jr"   : (Type.R,  0, 8   )
    }


    def __init__(self, name):
        """
        Opcode class constructor
        :param name: incoming instruction name to decode to opcode.
        """
        self.name = name


    def decode(self):
        """
        Decode the stored instruction name into its opcode integer part.
        :return: Integer representation of opcode.
        """
        try:
            return self.decoder[self.name]
        except KeyError:
            raise InvalidInstructionName(self.name)