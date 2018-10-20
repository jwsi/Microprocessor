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
                instruction = self.r_instruction(function)
                print(instruction)
            elif type == Type.I:
                # I instruction
                pass


            elif type == Type.J:
                # J instruction
                address = self.instruction[2]

        except KeyError:
            raise InvalidInstructionFormat()


    def r_instruction(self, function):
        """
        Given a function code this function will build an R instruction.
        :param function: function code of instruction.
        :return: List of byte strings representing instruction ready to insert into memory.
        """
        rs, rt, rd, shift, stage = 0, 0, 0, 0, 1 # By default set a no-op
        try:
            p1 = self.instruction[2]
            stage = 2
            p2 = self.instruction[3]
            stage = 3
            p3 = self.instruction[4]
        except IndexError: # Check instruction format.
            if function in [24, 26] and stage == 3:
                pass # Multiply & Divide only take 2 parameters as there is no destination register.
            else:
                raise InvalidInstructionFormat(self.instruction[1]) # Incorrect instruction format

        # Re order parameters
        if function in [24, 26] and stage == 3:
            rs, rt = p1, p2
        elif function in [0, 3]:  # SLL and SRA don't have source registers
            rd, rt, shift = p1, p2, p3
        else:
            rd, rs, rt = p1, p2, p3
        # Build byte list
        byte_list= ["{0:06b}".format(0) + "{0:05b}".format(rs)[0:2]]
        byte_list.append("{0:05b}".format(rs)[2:] + "{0:05b}".format(rt))
        byte_list.append("{0:05b}".format(rd) + "{0:05b}".format(shift)[0:3])
        byte_list.append("{0:05b}".format(shift)[3:] + "{0:06b}".format(function))
        return byte_list


    def i_instruction(self, ):
        pass

