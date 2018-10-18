from classes.opcode import Opcode, Type
from classes.errors import InvalidInstructionFormat


class Instruction():
    """
    Class for decoding assembly instructions into MIPS instructions.
    """
    instruction = None
    type = None


    def __init__(self, instruction):
        """
        Instruction class constructor.
        :param instruction: Incoming list containing assembly instruction parts.
        """
        self.instruction = instruction
        self.parse()


    def parse(self):
        """
        This function parses the assembly instruction object.
        :return: MIPS instruction object.
        """
        try:
            type, opcode, function = Opcode(self.instruction[1]).decode()
            if type == Type.R:
                # R instruction
                rd = self.instruction[2]
                rs = self.instruction[3]
                rt = self.instruction[4]
            elif type == Type.I:
                # I instruction
                rt = self.instruction[2]
                rs = self.instruction[3]
                immediate = self.instruction[4]
            elif type == Type.J:
                # J instruction
                address = self.instruction[2]
        except KeyError:
            raise InvalidInstructionFormat()


    def r_instruction(self, opcode, function):
        pass