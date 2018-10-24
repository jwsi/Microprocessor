from classes.opcode import Opcode

class Instruction():
    """
    Class for decoding machine instructions.
    """
    # Name and type of instruction
    name = None
    type = None

    # Potential operands of instruction
    rs = None
    rt = None
    rd = None
    imm = None
    shift = None
    address = None

    def __init__(self, raw_instruction):
        """
        Instruction class constructor.
        :param raw_instruction: String containing fetched instruction from memory.
        """
        self.raw_instruction = raw_instruction
        self.decode()


    def decode(self):
        """
        From the raw_instruction in the object,
        this function decodes a complete instruction into:
        opcode, type and operand parts.
        """
        opcode = int(self.raw_instruction[0:6], 2)
        function = None
        if opcode == "000000":
            function = int(self.raw_instruction[26:32], 2)
        self.name, self.type = Opcode(opcode, function).decode()
        print(self.name)