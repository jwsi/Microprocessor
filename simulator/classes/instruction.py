from classes.opcode import Opcode, Type

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
        self._decode_operands()


    def _decode_operands(self):
        """
        This function decodes operands based on the instruction type.
        """
        if self.type == Type.R:
            self._decode_r_operands()
        elif self.type == Type.I:
            self._decode_i_operands()
        elif self.type == Type.J:
            self._decode_j_operands()


    def _decode_r_operands(self):
        """
        Decodes R type operands.
        """
        self.rs = int(self.raw_instruction[6:11], 2)
        self.rt = int(self.raw_instruction[11:16], 2)
        self.rd = int(self.raw_instruction[16:21], 2)
        self.shift = int(self.raw_instruction[21:26], 2)


    def _decode_i_operands(self):
        """
        Decodes I type operands.
        """
        self.rs = int(self.raw_instruction[6:11], 2)
        self.rt = int(self.raw_instruction[11:16], 2)
        self.imm = int(self.raw_instruction[16:32], 2)


    def _decode_j_operands(self):
        """
        Decodes J type operands.
        """
        self.address = int(self.raw_instruction[6:32])
