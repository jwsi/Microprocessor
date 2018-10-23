# from enum import IntEnum, Enum
#
# # "{0:032b}".format(int.from_bytes(test, byteorder='little'))
#
# class OpCode(IntEnum):
#     """
#     This class defines all of the op-codes for each instruction used in the ISA on this simulator.
#     """
#     # R type instructions
#     ADD  = 0
#     SUB  = 0
#     AND  = 0
#     OR   = 0
#     XOR  = 0
#     NOR  = 0
#     SLT  = 0
#     SLL  = 0
#     SRA  = 0
#     MULT = 0
#     DIV  = 0
#     JR   = 0
#     # I type instructions
#     LW   = 35
#     SW   = 43
#     ANDI = 12
#     ADDI = 8
#     ORI  = 13
#     XORI = 14
#     SLTI = 10
#     LUI  = 15
#     BLEZ = 6
#     BGTZ = 7
#     BEQ  = 4
#     BNE  = 5
#     # J type instructions
#     J    = 2
#
#
# class InstructionType(Enum):
#     """
#     This class defines the types of instructions in MIPS core.
#     """
#     R = "R"
#     I = "I"
#     J = "J"
#
#
# class RInstruction():
#     """
#     This class represents an R Instruction in MIPS.
#     """
#     opcode = 0       # Fixed opcode of 0 for R instructions
#     rs = None        # Source Register
#     rt = None        # Secondary Register
#     rd = None        # Destination Register
#     shift_amount = 0 # Amount to shift by
#     function = None  # Function to perform
#     def __init__(self, **kwargs):
#         pass
#
#
# class IInstruction():
#     """
#     This class represents an I Instruction in MIPS.
#     """
#     opcode = None
#     rs = None # Source Register
#     rt = None # Secondary Register (or destination)
#     def __init__(self, **kwargs):
#         pass
#
#
# class JInstruction():
#     opcode = None
#     address = None # Address to jump to (absolute)
#     """
#     This class represents a J Instruction in MIPS
#     """
#     def __init__(self, **kwargs):
#         pass
#
#
# class UnknownInstructionType(Exception):
#     """
#     Unknown Instruction Type Exception.
#     """
#     pass
#
#
# class Instruction():
#     """
#     Instruction builder class.
#     """
#     def __init__(self, **kwargs):
#         type = kwargs.get("type")
#         if type == InstructionType.R:
#             RInstruction(**kwargs)
#         elif type == InstructionType.I:
#             IInstruction(**kwargs)
#         elif type == InstructionType.J:
#             JInstruction(**kwargs)
#         else:
#             raise UnknownInstructionType
#
