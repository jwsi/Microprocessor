import pickle
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit


class Simulator():
    memory = None
    pc = None

    clock = 0

    # Registers
    zero = 0 # register 0
    v0, v1 = 0, 0 # registers 2 to 3
    a0, a1, a2, a3 = 0, 0, 0, 0 # registers 4 to 7
    t0, t1, t2, t3, t4, t5, t6, t7 = 0, 0, 0, 0, 0, 0, 0, 0 # registers 8 to 15
    s0, s1, s2, s3, s4, s5, s6, s7 = 0, 0, 0, 0, 0, 0, 0, 0 # registers 16 to 23
    t8, t9 = 0, 0 # registers 24 to 25
    sp = 0 # register 29
    ra = 0 # register 31


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
        for i in range(4):
            raw_instruction += self.memory[self.pc+i]
        self.pc += 4
        return raw_instruction


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
        ExecutionUnit(instruction, self.memory).execute()


    def retire(self):
        pass

    def simulate(self):
        self.pc+=4
        raw_instruction = self.fetch()
        self.clock+=1
        instruction = self.decode(raw_instruction)
        self.clock+=1
        self.execute(instruction)
        self.clock+=1
        self.retire()
        self.clock+=1