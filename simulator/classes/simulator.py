import pickle
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile


class Simulator():
    """
    This is the class for the main processor simulator.
    """
    memory = None
    pc = None
    clock = 0
    register_file = RegisterFile().reg # Create the parent register file for the simulator

    def __init__(self, input_file):
        """
        Constructor for the Simulator class.
        :param input_file: input source machine code file.
        """
        f = open(input_file, "rb")
        self.memory = pickle.load(f)
        self.pc = pickle.load(f)
        self.register_file[29][1] = (max(self.memory) + 1) + (1000*4) # Initialise the stack pointer (1000 words).
        self.eu = ExecutionUnit(self.memory, self.register_file)
        f.close()


    def fetch(self):
        """
        This function fetches the appropriate instruction from memory.
        :return: raw binary instruction (string).
        """
        raw_instruction = ""
        try:
            for i in range(4):
                raw_instruction += self.memory[self.pc+i]
            return raw_instruction
        except KeyError:
            print(self.memory)
            print(self.register_file[2][:2], self.register_file[3][:2])
            exit(0)


    def decode(self, raw_instruction):
        """
        This function decodes the raw instruction into a Instruction object.
        :param raw_instruction: binary string of MIPS instruction.
        :return: Instruction object.
        """
        return Instruction(raw_instruction)


    def execute(self, instruction):
        """
        This function executes the Instruction object.
        :param instruction: Instruction object to be executed.
        """
        self.pc, queue = self.eu.execute(self.pc, instruction)
        return queue


    def retire(self, queue):
        """
        This function writes back the pending results from the EUs to the register file.
        :param queue: queue of writebacks.
        """
        queue.commit(self.register_file)


    def simulate(self):
        """
        The main simulate function controlling the:
        fetch, decode, execute and writeback commands.c
        """
        while True:
            raw_instruction = self.fetch()
            self.clock+=1
            instruction = self.decode(raw_instruction)
            self.clock+=1
            queue = self.execute(instruction)
            self.clock+=1
            self.retire(queue)
            self.clock+=1