class ExecutionUnit():
    # Each execution unit has its own register file...
    ins = None # Instruction to execute
    mem = None # Reference to simulator memory
    pending = None # Pending writeback to register


    def __init__(self, memory, registers):
        """
        Constructor for ExecutionUnit class.
        :param instruction: Instruction object to execute.
        :param memory: simulator main memory reference.
        """
        self.mem = memory
        self.reg = registers
        self.alu = self.ALU(self.reg)
        self.lsu = self.LSU(self.reg, self.mem)
        self.fpu = self.FPU(self.reg)
        self.beu = self.BEU(self.reg)


    def execute(self, pc, ins):
        """
        Executes the stored Instruction object.
        """
        # LOAD/STORE
        if ins.name in ["lw", "sw"]:
            self.lsu.execute(ins)
        # ALU Operations
        elif ins.name in ["add", "sub" "and", "or", "xor", "nor", "slt", "slti", "addi",
                               "andi", "ori", "xori", "lui", "sll", "sra"]:
            self.alu.execute(ins)
        # FPU Operations
        elif ins.name in ["mult", "div", "mfhi", "mflo"]:
            self.fpu.execute(ins)
        # Branch operations
        elif ins.name in ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]:
            return self.beu.execute(pc, ins)
        # All instructions bar branch pc += 4
        return pc + 4


    def writeback(self):
        pass


    class LSU():
        """
        This is the load store unit for the EU.
        """
        reg = None
        mem = None

        def __init__(self, registers, memory):
            """
            This is the constructor for the ALU inside the execution unit.
            """
            self.reg = registers
            self.mem = memory


        def execute(self, ins):
            """
            This function executes a load/store instruction.
            :param ins: Instruction object to execute.
            """
            if ins.name == "lw":
                # Load to the register rt the word found at (register_file(rs) + imm) in memory.
                self.reg[ins.rt][1] = self._get_word(self.reg[ins.rs][1] + ins.imm)
            elif ins.name == "sw":
                # Store to memory(rs + imm) the word found in the target register.
                self._store_word(self.reg[ins.rt][1], self.reg[ins.rs][1] + ins.imm)


        def _get_word(self, address):
            """
            This function retrieves a word from memory.
            :param address: Address of word.
            :return: Integer representation of word.
            """
            binary = self.mem[address]
            binary += self.mem[address + 1]
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
            self.mem[address] = binary[0:8]
            self.mem[address + 1] = binary[8:16]
            self.mem[address + 2] = binary[16:24]
            self.mem[address + 3] = binary[24:]


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
            elif ins.name == "sll":
                self.reg[ins.rd][1] = self.reg[ins.rt][1] << ins.shift
            elif ins.name == "sra":
                self.reg[ins.rd][1] = self.reg[ins.rt][1] >> ins.shift


    class FPU():
        """
        This is the floating point unit for the EU.
        """
        reg = None

        def __init__(self, registers):
            """
            This is the constructor for the FPU inside the execution unit.
            """
            self.reg = registers


        def execute(self, ins):
            """
            Given an FPU Instruction object, it will execute it.
            :param ins: Instruction object.
            """
            if ins.name == "mult":
                self.reg["lo"][1] = self.reg[ins.rs][1] * self.reg[ins.rt][1]
            elif ins.name == "div":
                self.reg["lo"][1] = self.reg[ins.rs][1] // self.reg[ins.rt][1]
                self.reg["hi"][1] = self.reg[ins.rs][1] % self.reg[ins.rt][1]
            elif ins.name == "mfhi":
                self.reg[ins.rd][1] = self.reg["hi"][1]
            elif ins.name == "mflo":
                self.reg[ins.rd][1] = self.reg["lo"][1]


    class BEU():
        """
        This is the branch execution unit for the EU.
        """
        reg = None

        def __init__(self, registers):
            """
            This is the constructor for the BEU inside the execution unit.
            """
            self.reg = registers


        def execute(self, pc, ins):
            """
            Given an BEU Instruction object, it will execute it.
            :param ins: Instruction object.
            """
            if ins.name == "beq":
                if self.reg[ins.rs][1] == self.reg[ins.rt][1]:
                    return pc + (ins.imm << 2)
            elif ins.name == "bne":
                if self.reg[ins.rs][1] != self.reg[ins.rt][1]:
                    return pc + (ins.imm << 2)
            elif ins.name == "blez":
                if self.reg[ins.rs][1] <= 0:
                    return pc + (ins.imm << 2)
            elif ins.name == "bgtz":
                if self.reg[ins.rs][1] > 0:
                    return pc + (ins.imm << 2)
            elif ins.name == "j":
                return ins.address
            elif ins.name == "jal":
                self.reg[31][1] = pc + 8
                return ins.address
            elif ins.name == "jr":
                return self.reg[ins.rs][1]
            return pc + 4

