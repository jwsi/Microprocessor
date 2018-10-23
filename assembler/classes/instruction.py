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


    def parse(self):
        """
        This function parses the assembly instruction object.
        :return: MIPS instruction object.
        """
        type, opcode, function = Opcode(self.instruction[0]).decode()

        if type == Type.R:
            instruction = self.r_instruction(function)
        elif type == Type.I:
            instruction = self.i_instruction(opcode)
        elif type == Type.J:
            instruction = self.j_instruction(opcode)
        return instruction


    def r_instruction(self, function):
        """
        Given a function code this function will build an R instruction.
        :param function: function code of instruction.
        :return: List of byte strings representing instruction ready to insert into memory.
        """
        rs, rt, rd, shift, stage = 0, 0, 0, 0, 1 # By default set a no-op
        try:
            p1, o1 = self.instruction[1]
            stage = 2
            p2, o2 = self.instruction[2]
            stage = 3
            p3, o3 = self.instruction[3]
        except IndexError: # Check instruction format.
            if function in [8, 16, 18] and stage == 2:
                pass # JR, MFHI, MFLO only take 1 parameter.
            elif function in [24, 26] and stage == 3:
                pass # Multiply & Divide only take 2 parameters as there is no destination register.
            else:
                raise InvalidInstructionFormat(self.instruction[0]) # Incorrect instruction format
        # Re order parameters
        if function in [24, 26]:
            rs, rt = p1, p2
        elif function in [0, 3]:  # SLL and SRA don't have source registers
            rd, rt, shift = p1, p2, p3
        elif function == 8:
            rs = p1
        elif function in [16, 18]:
            rd = p1
        else:
            rd, rs, rt = p1, p2, p3
        # Build byte list
        byte_list= ["{0:06b}".format(0) + "{0:05b}".format(rs)[0:2]]
        byte_list.append("{0:05b}".format(rs)[2:] + "{0:05b}".format(rt))
        byte_list.append("{0:05b}".format(rd) + "{0:05b}".format(shift)[0:3])
        byte_list.append("{0:05b}".format(shift)[3:] + "{0:06b}".format(function))
        return byte_list


    def i_instruction(self, opcode):
        """
        Given an opcode this function will build an I instruction.
        :param opcode: opcode of instruction.
        :return: List of byte strings representing instruction ready to insert into memory.
        """
        rs, rt, imm, stage = 0, 0, 0, 1  # By default set a no-op
        try:
            p1, o1 = self.instruction[1]
            stage = 2
            p2, o2 = self.instruction[2]
            stage = 3
            p3, o3 = self.instruction[3]
        except IndexError:
            if opcode in [6, 7, 15, 35, 43] and stage == 3:
                pass # LW, SW, BGTZ, LUI & BLEZ only take two params.
            else:
                raise InvalidInstructionFormat(self.instruction[0])  # Incorrect instruction format

        # Re order parameters
        if opcode in [6, 7]: # BGTZ & BLEZ only take source and imm.
            rs, imm = p1, p2
        elif opcode in [4, 5]: # Source is first on BEQ and BNE.
            rs, rt, imm = p1, p2, p3
        elif opcode in [15]: # LUI only takes target and immediate
            rt, imm = p1, p2
        elif opcode in [35, 43]: # LW & SW only takes two params with an offset.
            if p2 >= 32:
                rt, imm = p1, (p2+o2) # Load from variable
            else:
                rt, rs, imm = p1, p2, o2 # Load address from register with offset
        else:
            rt, rs, imm = p1, p2, p3
        # Build byte list
        byte_list = ["{0:06b}".format(opcode) + "{0:05b}".format(rs)[0:2]]
        byte_list.append("{0:05b}".format(rs)[2:] + "{0:05b}".format(rt))
        byte_list.append("{0:016b}".format(imm)[0:8])
        byte_list.append("{0:016b}".format(imm)[8:])
        return byte_list


    def j_instruction(self, opcode):
        """
        Given an opcode this function will build a J instruction.
        :param opcode: opcode of instruction.
        :return: List of byte strings representing instruction ready to insert into memory.
        """
        try:
            addr, _ = self.instruction[1]
        except IndexError:
            raise InvalidInstructionFormat(self.instruction[0])
        byte_list = ["{0:06b}".format(opcode) + "{0:026b}".format(addr)[0:2]]
        byte_list.append("{0:026b}".format(addr)[2:10])
        byte_list.append("{0:026b}".format(addr)[10:18])
        byte_list.append("{0:026b}".format(addr)[18:26])
        return byte_list

