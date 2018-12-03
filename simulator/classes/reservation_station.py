from classes.instruction import Type
import curses

class ReservationStation:
    """
    Reservation station class to store instructions pending execution.
    """
    def __init__(self):
        """
        Constructor for the reservation station class.
        """
        self.queue = []


    def get_ready_instructions(self):
        """
        This function will return the oldest ready instruction.
        :return: Instruction or None depending on whether the instruction is ready to be executed.
        """
        self._update_dependencies()
        instructions = []
        for _ in range(4):
            try:
                if self.queue[0]["ready"]:
                    instructions.append(self.queue.pop(0)["instruction"])
                else:
                    break
            except IndexError:
                break
        return instructions


    def add_instruction(self, instruction):
        """
        This function will add an instruction to the reservation station.
        """
        self.queue.append({
            "instruction" : instruction,
            "ready" : True
        })


    def clear(self):
        """
        This function will clear the entire reservation station queue.
        """
        self.queue = []


    def _update_dependencies(self):
        """
        This function will update the dependencies of the pending next step instructions.
        """
        for i in range(min(4, len(self.queue))):
            self.queue[i]["ready"] = True # Clear previous dependencies
        reads = self._get_reads()
        writes = self._get_writebacks()
        for i in range(min(4, len(self.queue))): # Set dependencies based on reads and writes
            for j in range(i+1, min(4, len(self.queue))):
                if set(writes[i]) & set(reads[j]):
                    self.queue[j]["ready"] = False
        self._hardware_limitation()


    def _get_reads(self):
        """
        This function calculates the read registers for pending next step instructions.
        :return: List of read registers.
        """
        reads = [[] for _ in range(4)]
        for i in range(min(4, len(self.queue))):  # Add read dependencies
            instruction = self.queue[i]["instruction"]
            if instruction.type == Type.I:
                reads[i].append(instruction.rs)
            elif instruction.type == Type.R:
                if instruction.name == "mfhi":
                    reads[i].append(32)
                elif instruction.name == "mflo":
                    reads[i].append(33)
                else:
                    reads[i].append(instruction.rs)
                    reads[i].append(instruction.rt)
            reads[i] = [i for i in reads[i] if (i != 0 and i is not None)]  # Remove irrelevant reads
        return reads


    def _get_writebacks(self):
        """
        This function calculates the writeback registers for pending next step instructions.
        :return: List of writeback registers.
        """
        writebacks = [[] for _ in range(4)]
        for i in range(min(4, len(self.queue))):  # Add writeback dependencies
            instruction = self.queue[i]["instruction"]
            if instruction.type == Type.I:
                writebacks[i].append(instruction.rt)
            elif instruction.type == Type.R:
                if instruction.name == "mult": # Special case for MULT
                    writebacks[i].append(33)
                elif instruction.name == "div": # Special case for DIV
                    writebacks[i].append(33)
                    writebacks[i].append(32)
                else:
                    writebacks[i].append(instruction.rd)
            elif instruction.type == Type.J:
                if instruction.name == "jal": # Special case for JAL
                    writebacks[i].append(31)
            writebacks[i] = [i for i in writebacks[i] if (i != 0 and i is not None)] # Remove irrelevant writebacks
        return writebacks


    def _hardware_limitation(self):
        """
        Will change the ready flag of instructions in the reservation station to reflect hardware limitations.
        """
        lsu_list = ["lw", "sw"]
        beu_list = ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]
        lsu_instructions, beu_instructions, alu_instructions = [], [], []
        for i in range(min(4, len(self.queue))):
            instruction = self.queue[i]["instruction"]
            if instruction.name in lsu_list and self.queue[i]["ready"]:
                lsu_instructions.append(i)
            elif instruction.name in beu_list and self.queue[i]["ready"]:
                beu_instructions.append(i)
            elif self.queue[i]["ready"]:
                alu_instructions.append(i)
        if len(lsu_instructions) > 1:
            for ins in lsu_instructions[1:]:
                self.queue[ins]["ready"] = False
        if len(beu_instructions) > 1:
            for ins in beu_instructions[1:]:
                self.queue[ins]["ready"] = False
        if len(alu_instructions) > 2:
            for ins in alu_instructions[2:]:
                self.queue[ins]["ready"] = False


    def print(self, stdscr):
        """
        Prints the contents of the reservation station to the terminal.
        :param stdscr: terminal to print to.
        """
        stdscr.addstr(2, 150, "RESERVATION STATION".ljust(56), curses.color_pair(3))
        stdscr.addstr(2, 150, "Pending Instructions: " + str(len(self.queue)).ljust(56), curses.color_pair(3))
        for i in range(30):
            stdscr.addstr(4 + i, 150, "".ljust(50))
        for i in range(len(self.queue)):
            stdscr.addstr(4 + i, 150, self.queue[i]["instruction"].name.ljust(50), curses.color_pair(3))


