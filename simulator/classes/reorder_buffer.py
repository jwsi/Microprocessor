from classes.constants import N
from classes.errors import ResultNotReady
import curses

class ReOrderBuffer:
    """
    Class representing the re-order buffer.
    """
    def __init__(self):
        """
        Constructor for the Re-Order Buffer class.
        """
        self.queue = { # Define a dictionary representing the re-order buffer queue
            # ID : { "ready" : w, "instruction" : x, "result" : { y }, "written" : z }
        }


    def insert_entry(self, instruction):
        """
        Inserts an instruction into the re-order buffer.
        :param Instruction: Instruction to insert.
        :return: Key at which the instruction is stored in the ROB.
        """
        key = self._next_available_key()
        self.queue[key] = {
            "ready" : False,
            "written" : False,
            "instruction" : instruction,
            "result" : {}
        }
        return key


    def _next_available_key(self):
        """
        Calculates the next available key in the ROB.
        :return: Next available key.
        """
        try:
            return max(self.queue.keys()) + 1 # We can do this as all keys are integers
        except ValueError: # ROB is empty
            return 0


    def get_finished_instructions(self):
        """
        Gets up to N finished instructions from the ROB.
        Ready instructions are returned sequentially for writeback to ensure program correctness.
        :return: Instructions that have finished execution and are ready to be written back.
        """
        instructions = []
        for key in range(len(self.queue)):
            if len(instructions) == N:
                break
            elif self.queue[key]["ready"] and not self.queue[key]["written"]:
                instructions.append(self.queue[key])
            elif self.queue[key]["ready"]:
                continue
            else:
                break
        return instructions


    def clear_after(self, rob_entry):
        """
        Clears all instructions after a ROB entry.
        :param rob_entry: Last entry to consider valid.
        """
        for i in range(rob_entry+1, len(self.queue)):
            del self.queue[i]


    def no_writebacks(self):
        """
        Checks if there are any pending writebacks in the re-order buffer.
        :return: Boolean representing whether writebacks are pending.
        """
        for key, value in self.queue.items():
            if not value["written"]:
                return False
        return True


    def get_result(self, rob_entry, register):
        """
        Gets the result for a register in a particular ROB entry.
        :param rob_entry: Entry to get result from.
        :param register: Register in the result dictionary one wishes to obtain.
        :return: Value of register selected.
        """
        if self.queue[rob_entry]["ready"]:
            return self.queue[rob_entry]["result"][register]
        raise ResultNotReady("Result is not yet ready for ROB entry: " + str(rob_entry))


    def write_result(self, rob_entry, register, result):
        """
        Writes the result for an instruction to an entry in the ROB.
        :param rob_entry: ROB entry to write the result to.
        :param register: Register to which the result belongs.
        :param result: Result of the execution.
        """
        self.queue[rob_entry]["result"][register] = result


    def mark_ready(self, rob_entry):
        """
        Mark a ROB entry as ready.
        :param rob_entry: ROB entry to mark.
        """
        self.queue[rob_entry]["ready"] = True


    def mark_written(self, rob_entry):
        """
        Mark a ROB entry as written.
        :param rob_entry: ROB entry to mark.
        """
        self.queue[rob_entry]["written"] = True


    def print(self, stdscr):
        """
        This prints the re-order buffer to the terminal provided.
        :param stdscr: Terminal to print the re-order buffer to.
        """
        stdscr.addstr(23, 100, "REORDER BUFFER".ljust(48), curses.color_pair(7))
        for i in range(26):
            stdscr.addstr(25 + i, 100, "".ljust(72))
        display = {}
        for key in self.queue.keys():
            try:
                if self.queue[key+10]["ready"] and self.queue[key+10]["written"]:
                    continue
            except KeyError:
                pass
            if len(display) < 26:
                display[key] = self.queue[key]
        i = 0
        for key in display.keys():
            if display[key]["ready"]:
                prefix_r = "\u2713 "
            else:
                prefix_r = "\u002E "
            if display[key]["written"]:
                prefix_w = "\u2713 "
            else:
                prefix_w = "\u002E "
            stdscr.addstr(25 + i, 100,
                          "id: " + str(key) + " r: " + prefix_r + " w: " + prefix_w +
                          display[key]["instruction"].description().ljust(56),
                          curses.color_pair(7))
            i += 1
