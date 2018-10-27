import pickle
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit


class Simulator():
    memory = None
    pc = None

    clock = 0

    reg = {
        0: ["zero", 0],
        8: ["t0", 0],
        9: ["t1", 0],
        10: ["t2", 0],
        11: ["t3", 0],
        12: ["t4", 0],
        13: ["t5", 0],
        14: ["t6", 0],
        15: ["t7", 0],
        24: ["t8", 0],
        25: ["t9", 0],
        29: ["sp", 0],
        31: ["ra", 0],
        "hi": ["hi", 0],
        "lo": ["lo", 0]
    }

    def __init__(self, input_file):
        """
        Constructor for the Simulator class.
        :param input_file: input source machine code file.
        """
        f = open(input_file, "rb")
        self.memory = pickle.load(f)
        self.pc = pickle.load(f)
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
        self.pc = ExecutionUnit(self.memory, self.reg).execute(self.pc, instruction)


    def retire(self):
        pass

    def simulate(self):
        while True:
            raw_instruction = self.fetch()
            self.clock+=1
            instruction = self.decode(raw_instruction)
            self.clock+=1
            self.execute(instruction)
            self.clock+=1
            self.retire()
            self.clock+=1