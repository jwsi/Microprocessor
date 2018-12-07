from classes.constants import N

class ReOrderBuffer:
    """
    Class representing the re-order buffer.
    """
    def __init__(self):
        """
        Constructor for the Re-Order Buffer class.
        """
        self.queue = { # Define a dictionary representing the re-order buffer queue
            # ID : { "ready" : status, "instruction" : ins, "result" : execution_result }
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