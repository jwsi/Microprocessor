from classes.instruction import Type
import curses
from classes.constants import N

class ReservationStation:
    """
    Reservation station class to store instructions pending execution.
    """
    def __init__(self, reorder_buffer):
        """
        Constructor for the reservation station class.
        """
        self.queue = []
        self.reorder_buffer = reorder_buffer


    def get_ready_instructions(self):
        """
        This function will return the oldest ready instruction.
        :return: Instruction or None depending on whether the instruction is ready to be executed.
        """
        self._update_dependencies()
        instructions = []
        for i in range(len(self.queue)):
            try:
                if len(instructions) >= N:
                    break
                while self.queue[i]["ready"]:
                    instructions.append(self.queue.pop(i)["instruction"])
            except IndexError:
                break
        return instructions


    def add_instruction(self, instruction):
        """
        This function will add an instruction to the reservation station.
        """
        self.queue.append({
            "instruction" : instruction,
            "ready" : self._calculate_readyness(instruction)
        })


    def _calculate_readyness(self, instruction):
        """
        Given an instruction, this function will determine if it is ready to be executed.
        :param instruction: Instruction to determine readyness of.
        :return: Boolean representing whether instruction is ready to be executed.
        """
        valid_rs = False
        valid_rt = False
        if instruction.operands["rs"] == {} or instruction.operands["rs"]["valid"]:
            valid_rs = True
        elif self.reorder_buffer.queue[instruction.operands["rs"]["value"]]["ready"]:
            valid_rs = True
        if instruction.operands["rt"] == {} or instruction.operands["rt"]["valid"]:
            valid_rt = True
        elif self.reorder_buffer.queue[instruction.operands["rt"]["value"]]["ready"]:
            valid_rt = True
        return valid_rs & valid_rt


    def clear_block(self, instruction_block):
        """
        This function will clear the entire reservation station queue.
        """
        for i in range(len(self.queue)):
            try:
                while self.queue[i]["instruction"].block >= instruction_block:
                    del self.queue[i]
            except IndexError:
                break


    def _update_dependencies(self):
        """
        This function will update the dependencies of the pending instructions.
        """
        for item in self.queue:
            item["ready"] = self._calculate_readyness(item["instruction"]) # Clear previous dependencies
        self._hardware_limitation()


    def _hardware_limitation(self):
        """
        Will change the ready flag of instructions in the reservation station to reflect hardware limitations.
        """
        lsu_list = ["lw", "sw"]
        beu_list = ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]
        lsu_instructions, beu_instructions, alu_instructions = [], [], []
        for i in range(len(self.queue)):
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
        self._update_dependencies()
        stdscr.addstr(0, 150, "RESERVATION STATION".ljust(48), curses.color_pair(6))
        stdscr.addstr(2, 150, "Pending Instructions: " + str(len(self.queue)).ljust(24), curses.color_pair(6))
        for i in range(16):
            stdscr.addstr(4 + i, 150, "".ljust(52))
        for i in range(min(16, len(self.queue))):
            if self.queue[i]["ready"]:
                prefix = "\u2713 "
            else:
                prefix = "\u002E "
            stdscr.addstr(4 + i, 150,
                          "r: " + prefix +
                          self.queue[i]["instruction"].description().ljust(48),
                          curses.color_pair(6))


