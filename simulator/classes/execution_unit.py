from classes.register_file import RegisterFile
from classes.errors import Interrupt, UnsupportedInstruction, AlreadyExecutingInstruction


class ExecutionUnit():
    def __init__(self, memory, registers, alu=True, lsu=True, fpu=True, beu=True):
        """
        Constructor for ExecutionUnit class.
        :param instruction: Instruction object to execute.
        :param memory: simulator main memory reference.
        """
        self.mem = memory
        self.reg = registers # Each EU has it's own register file.
        self.busy_subunits = []
        # Define capabilities of execution unit.
        if alu:
            self.alu = self.ALU(self.reg)
        if lsu:
            self.lsu = self.LSU(self.reg, self.mem)
        if fpu:
            self.fpu = self.FPU(self.reg)
        if beu:
            self.beu = self.BEU(self.reg)


    def execute(self, ins):
        """
        Executes the stored Instruction object.
        """
        queue = RegisterFile()
        try:
            # LOAD/STORE
            if ins.name in ["lw", "sw"]:
                self._check_subunit_status("lsu")
                self.lsu.execute(ins, queue)
            # ALU Operations
            elif ins.name in ["add", "sub" "and", "or","xor", "nor", "slt", "slti",
                               "addi", "andi", "ori", "xori", "lui", "sll", "sra"]:
                self._check_subunit_status("alu")
                self.alu.execute(ins, queue)
            # FPU Operations
            elif ins.name in ["mult", "div", "mfhi", "mflo"]:
                self._check_subunit_status("fpu")
                self.fpu.execute(ins, queue)
            # Branch operations
            elif ins.name in ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]:
                self._check_subunit_status("beu")
                return self.beu.execute(ins, queue), queue
            # Syscall
            elif ins.name == "syscall":
                raise Interrupt()
            # All instructions bar branch pc += 4
            return ins.pc + 4, queue
        # Catch instructions that cannot be executed by this EU.
        except AttributeError:
            raise UnsupportedInstruction("`" + ins.name + "` on EU: " + str(id(self)))


    def _check_subunit_status(self, subunit):
        """
        Checks if a EU subunit is busy. If it is, an exception is raised. Otherwise it is marked as busy.
        :param subunit: String representing subunit.
        """
        if subunit in self.busy_subunits:
            raise AlreadyExecutingInstruction(str(subunit) + " on EU: " + str(id(self)))
        self.busy_subunits.append(subunit)


    def clear_subunits(self):
        """
        Marks all subunits as free for execution again.
        """
        self.busy_subunits = []


    class LSU():
        """
        This is the load store unit for the EU.
        """
        def __init__(self, registers, memory):
            """
            This is the constructor for the ALU inside the execution unit.
            """
            self.reg = registers
            self.mem = memory


        def execute(self, ins, queue):
            """
            This function executes a load/store instruction.
            :param ins: Instruction object to execute.
            """
            if ins.name == "lw":
                # Load to the register rt the word found at (register_file(rs) + imm) in memory.
                queue.write(ins.rt, self._get_word(self.reg[ins.rs][1] + ins.imm))
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
        def __init__(self, registers):
            """
            This is the constructor for the ALU inside the execution unit.
            """
            self.reg = registers


        def execute(self, ins, queue):
            """
            Given an ALU Instruction object, it will execute it.
            :param ins: Instruction object.
            """
            if ins.name == "add":
                queue.write(ins.rd, self.reg[ins.rs][1] + self.reg[ins.rt][1])
            elif ins.name == "sub":
                queue.write(ins.rd, self.reg[ins.rs][1] - self.reg[ins.rt][1])
            elif ins.name == "and":
                queue.write(ins.rd, self.reg[ins.rs][1] & self.reg[ins.rt][1])
            elif ins.name == "or":
                queue.write(ins.rd, self.reg[ins.rs][1] | self.reg[ins.rt][1])
            elif ins.name == "xor":
                queue.write(ins.rd, self.reg[ins.rs][1] ^ self.reg[ins.rt][1])
            elif ins.name == "nor":
                queue.write(ins.rd, ~(self.reg[ins.rs][1] | self.reg[ins.rt][1]))
            elif ins.name == "slt":
                queue.write(ins.rd, int(self.reg[ins.rs][1] < self.reg[ins.rt][1]))
            elif ins.name == "slti":
                queue.write(ins.rt, int(self.reg[ins.rs][1] < ins.imm))
            elif ins.name == "addi":
                queue.write(ins.rt, self.reg[ins.rs][1] + ins.imm)
            elif ins.name == "andi":
                queue.write(ins.rt, self.reg[ins.rs][1] & ins.imm)
            elif ins.name == "ori":
                queue.write(ins.rt, self.reg[ins.rs][1] | ins.imm)
            elif ins.name == "xori":
                queue.write(ins.rt, self.reg[ins.rs][1] ^ ins.imm)
            elif ins.name == "lui":
                queue.write(ins.rt, ins.imm << 16)
            elif ins.name == "sll":
                queue.write(ins.rd, self.reg[ins.rt][1] << ins.shift)
            elif ins.name == "sra":
                queue.write(ins.rd, self.reg[ins.rt][1] >> ins.shift)


    class FPU():
        """
        This is the floating point unit for the EU.
        """
        def __init__(self, registers):
            """
            This is the constructor for the FPU inside the execution unit.
            """
            self.reg = registers


        def execute(self, ins, queue):
            """
            Given an FPU Instruction object, it will execute it.
            :param ins: Instruction object.
            """
            if ins.name == "mult":
                queue.write(33, self.reg[ins.rs][1] * self.reg[ins.rt][1])
            elif ins.name == "div":
                queue.write(33, self.reg[ins.rs][1] // self.reg[ins.rt][1])
                queue.write(32, self.reg[ins.rs][1] % self.reg[ins.rt][1])
            elif ins.name == "mfhi":
                queue.write(ins.rd, self.reg[32][1])
            elif ins.name == "mflo":
                queue.write(ins.rd, self.reg[33][1])


    class BEU():
        """
        This is the branch execution unit for the EU.
        """
        def __init__(self, registers):
            """
            This is the constructor for the BEU inside the execution unit.
            """
            self.reg = registers


        def execute(self, ins, queue):
            """
            Given an BEU Instruction object, it will execute it.
            :param ins: Instruction object.
            """
            if ins.name == "beq":
                if self.reg[ins.rs][1] == self.reg[ins.rt][1]:
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "bne":
                if self.reg[ins.rs][1] != self.reg[ins.rt][1]:
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "blez":
                if self.reg[ins.rs][1] <= 0:
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "bgtz":
                if self.reg[ins.rs][1] > 0:
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "j":
                return ins.address
            elif ins.name == "jal":
                queue.write(31, ins.pc + 4)
                return ins.address
            elif ins.name == "jr":
                return self.reg[ins.rs][1]
            return ins.pc + 4