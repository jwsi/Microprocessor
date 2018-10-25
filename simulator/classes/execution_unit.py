class ExecutionUnit():
    # Each execution unit has its own register file...
    reg = {
        0:  ["zero", 0],
        8:  ["t0", 0],
        9:  ["t1", 0],
        10: ["t2", 0],
        11: ["t3", 0],
        12: ["t4", 0],
        13: ["t5", 0],
        14: ["t6", 0],
        15: ["t7", 0],
        24: ["t8", 0],
        25: ["t9", 0],
        29: ["sp", 0],
        31: ["ra", 0]
    }
    ins = None # Instruction to execute
    mem = None # Reference to simulator memory
    _result = None # Stores the result prior to the writeback stage.


    def __init__(self, instruction, memory):
        """
        Constructor for ExecutionUnit class.
        :param instruction: Instruction object to execute.
        :param memory: simulator main memory reference.
        """
        self.ins = instruction
        self.mem = memory


    def execute(self):
        """
        Executes the stored Instruction object.
        :return:
        """
        # Filter into: LOAD/STORE, ALU, SHIFT, MULT/DIV, JUMP/BRANCH
        if self.ins.name in ["lw", "sw"]:
            self._load_store()
        elif self.ins.name in ["add", "sub" "and", "or", "xor", "nor", "slt",
                               "slti", "addi", "andi", "ori", "xori", "lui"]:
            self.ALU()


    def _load_store(self):
        """
        This function handles load and store operations.
        """
        if self.ins.name == "lw":
            # Load to the register rt the word found at (register_file(rs) + imm) in memory.
            self.reg[self.ins.rt][1] = self._get_word(self.reg[self.ins.rs][1] + self.ins.imm)
        elif self.ins.name == "sw":
            # Store to memory(rs + imm) the word found in the target register.
            self._store_word(self.reg[self.ins.rt][1], self.reg[self.ins.rs][1] + self.ins.imm)


    def _get_word(self, address):
        """
        This function retrieves a word from memory.
        :param address: Address of word.
        :return: Integer representation of word.
        """
        binary = self.mem[address]
        binary +=self.mem[address + 1]
        binary += self.mem[address + 2]
        binary += self.mem[address + 3]
        return int(binary, 2)


    def _store_word(self, value, address):
        """
        This function stores a word in memory.
        :param value: Integer representation of value to store.
        :param address: Address to store word at.
        """
        binary = "{0:032b}".format(value)
        self.mem[address]     = binary[0:8]
        self.mem[address + 1] = binary[8:16]
        self.mem[address + 2] = binary[16:24]
        self.mem[address + 3] = binary[24:]


    def writeback(self):
        """
        Writeback the result to the register file.
        :return:
        """
        pass


    class ALU():
        """
        This is the Arithmetic Logic unit for the EU.
        """
        reg = None

        def __init__(self, registers):
            """
            This is the constructor for the ALU inside the execution unit.
            """
            self.reg = registers


        def execute(self, ins):
            """
            Given an ALU Instruction object, it will execute it.
            :param ins: Instruction object.
            :return:
            """
            if ins.name == "add":
                self.reg[ins.rd][1] = self.reg[ins.rs][1] + self.reg[ins.rt][1]
            elif ins.name == "sub":
                self.reg[ins.rd][1] = self.reg[ins.rs][1] - self.reg[ins.rt][1]
            elif ins.name == "and":
                self.reg[ins.rd][1] = self.reg[ins.rs][1] & self.reg[ins.rt][1]
            elif ins.name == "or":
                self.reg[ins.rd][1] = self.reg[ins.rs][1] | self.reg[ins.rt][1]
            elif ins.name == "xor":
                self.reg[ins.rd][1] = self.reg[ins.rs][1] ^ self.reg[ins.rt][1]
            elif ins.name == "nor":
                self.reg[ins.rd][1] = ~(self.reg[ins.rs][1] | self.reg[ins.rt][1])
            elif ins.name == "slt":
                self.reg[ins.rd][1] = int(self.reg[ins.rs][1] < self.reg[ins.rt][1])
            elif ins.name == "slti":
                self.reg[ins.rt][1] = int(self.reg[ins.rs][1] < ins.imm)
            elif ins.name == "addi":
                self.reg[ins.rt][1] = self.reg[ins.rs][1] + ins.imm
            elif ins.name == "andi":
                self.reg[ins.rt][1] = self.reg[ins.rs][1] & ins.imm
            elif ins.name == "ori":
                self.reg[ins.rt][1] = self.reg[ins.rs][1] | ins.imm
            elif ins.name == "xori":
                self.reg[ins.rt][1] = self.reg[ins.rs][1] ^ ins.imm
            elif ins.name == "lui":
                self.reg[ins.rt][1] = ins.imm << 16



