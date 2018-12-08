from classes.errors import Interrupt, UnsupportedInstruction, AlreadyExecutingInstruction
from classes.branch_predictor import BranchPredictor


class ExecutionUnit():
    def __init__(self, memory, registers, alu=True, lsu=True, beu=True):
        """
        Constructor for ExecutionUnit class.
        :param instruction: Instruction object to execute.
        :param memory: simulator main memory reference.
        :param alu: ALU capability.
        :param lsu: LSU capability.
        :param beu: BEU capability.
        """
        self.mem = memory
        self.reg = registers # Each EU has it's own register file.
        self.busy_subunits = []
        # Define capabilities of execution unit.
        if alu:
            self.alu = self.ALU()
        if lsu:
            self.lsu = self.LSU(self.mem)
        if beu:
            self.beu = self.BEU()


    def execute(self, ins, rob):
        """
        Executes the stored Instruction object.
        :param ins: instruction to execute.
        :param rob: re-order buffer.
        """
        source, target = self._get_operands(ins, rob)
        try:
            # LOAD/STORE
            if ins.name in ["lw", "sw"]:
                self._check_subunit_status("lsu")
                self.lsu.execute(ins, source, target, rob)
            # ALU Operations
            elif ins.name in ["add", "sub" "and", "or","xor", "nor", "slt", "slti",
                              "addi", "andi", "ori", "xori", "lui", "sll", "sra",
                              "mult", "div", "mfhi", "mflo"]:
                self._check_subunit_status("alu")
                self.alu.execute(ins, source, target, rob)
            # Branch operations
            elif ins.name in ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]:
                self._check_subunit_status("beu")
                return self.beu.execute(ins, source, target, rob)
            # All instructions bar branch pc += 4
            return ins.pc + 4
        # Catch instructions that cannot be executed by this EU.
        except AttributeError:
            raise UnsupportedInstruction("`" + ins.name + "` on EU: " + str(id(self)))
        # Mark the instruction as ready for writeback.
        finally:
            rob.mark_ready(ins.rob_entry)



    def _get_operands(self, ins, rob):
        """
        This function returns the most up to date values for operands of an instruction.
        :param ins: instruction to get operands for.
        :param rob: re-order buffer.
        :return: source and target register values.
        """
        source, target = None, None
        if ins.operands["rs"] != {}:
            if ins.operands["rs"]["valid"]:
                source = ins.operands["rs"]["value"]
            else:
                source = rob.get_result(ins.operands["rs"]["value"], ins.rs)
        if ins.operands["rt"] != {}:
            if ins.operands["rt"]["valid"]:
                target = ins.operands["rt"]["value"]
            else:
                target = rob.get_result(ins.operands["rt"]["value"], ins.rt)
        return source, target


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
        def __init__(self, memory):
            """
            This is the constructor for the ALU inside the execution unit.
            """
            self.mem = memory


        def execute(self, ins, source, target, rob):
            """
            This function executes a load/store instruction.
            :param ins: Instruction object to execute.
            :param source: source operand to execute with.
            :param target: target operand to execute with.
            :param rob: re-order buffer.
            """
            if ins.name == "lw":
                # Load to the register rt the word found at (register_file(rs) + imm) in memory.
                rob.write_result(ins.rob_entry, ins.rt, self._get_word(source + ins.imm))
            elif ins.name == "sw":
                # Store to memory(rs + imm) the word found in the target register.
                self._store_word(target, source + ins.imm)


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
        def execute(self, ins, source, target, rob):
            """
            Given an ALU Instruction object, it will execute it.
            :param ins: Instruction object.
            :param source: source operand to execute with.
            :param target: target operand to execute with.
            :param rob: re-order buffer.
            """
            if ins.name == "add":
                rob.write_result(ins.rob_entry, ins.rd, source + target)
            elif ins.name == "sub":
                rob.write_result(ins.rob_entry, ins.rd, source - target)
            elif ins.name == "and":
                rob.write_result(ins.rob_entry, ins.rd, source & target)
            elif ins.name == "or":
                rob.write_result(ins.rob_entry, ins.rd, source | target)
            elif ins.name == "xor":
                rob.write_result(ins.rob_entry, ins.rd, source ^ target)
            elif ins.name == "nor":
                rob.write_result(ins.rob_entry, ins.rd, ~(source | target))
            elif ins.name == "slt":
                rob.write_result(ins.rob_entry, ins.rd, int(source < target))
            elif ins.name == "slti":
                rob.write_result(ins.rob_entry, ins.rt, int(source < ins.imm))
            elif ins.name == "addi":
                rob.write_result(ins.rob_entry, ins.rt, source + ins.imm)
            elif ins.name == "andi":
                rob.write_result(ins.rob_entry, ins.rt, source & ins.imm)
            elif ins.name == "ori":
                rob.write_result(ins.rob_entry, ins.rt, source | ins.imm)
            elif ins.name == "xori":
                rob.write_result(ins.rob_entry, ins.rt, source ^ ins.imm)
            elif ins.name == "lui":
                rob.write_result(ins.rob_entry, ins.rt, ins.imm << 16)
            elif ins.name == "sll":
                rob.write_result(ins.rob_entry, ins.rd, target << ins.shift)
            elif ins.name == "sra":
                rob.write_result(ins.rob_entry, ins.rd, target >> ins.shift)
            elif ins.name == "mult":
                rob.write_result(ins.rob_entry, 33, source * target)
            elif ins.name == "div":
                rob.write_result(ins.rob_entry, 33, source // target)
                rob.write_result(ins.rob_entry, 32, source % target)
            elif ins.name == "mfhi":
                # Source is HI for this instruction.
                rob.write_result(ins.rob_entry, ins.rd, source)
            elif ins.name == "mflo":
                # Source is LO for this instruction.
                rob.write_result(ins.rob_entry, ins.rd, source)


    class BEU():
        """
        This is the branch execution unit for the EU.
        """
        def __init__(self):
            """
            This is the constructor for the BEU inside the execution unit.
            """
            self.branch_predictor = BranchPredictor()


        def execute(self, ins, source, target, rob):
            """
            Given an BEU Instruction object, it will execute it.
            :param ins: Instruction object.
            :param source: source operand to execute with.
            :param target: target operand to execute with.
            :param rob: re-order buffer.
            """
            if ins.name == "beq":
                if source == target:
                    self.branch_predictor.update_prediction(True)
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "bne":
                if source != target:
                    self.branch_predictor.update_prediction(True)
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "blez":
                if source <= 0:
                    self.branch_predictor.update_prediction(True)
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "bgtz":
                if source > 0:
                    self.branch_predictor.update_prediction(True)
                    return ins.pc + (ins.imm << 2)
            elif ins.name == "j":
                return ins.address
            elif ins.name == "jal":
                rob.write_result(ins.rob_entry, 31, ins.pc + 4)
                return ins.address
            elif ins.name == "jr":
                return source
            self.branch_predictor.update_prediction(False)
            return ins.pc + 4