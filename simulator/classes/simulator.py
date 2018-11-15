import pickle, curses
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

    def __init__(self, input_file, stdscr):
        """
        Constructor for the Simulator class.
        :param input_file: input source machine code file.
        """
        f = open(input_file, "rb")
        self.memory = pickle.load(f)
        self.pc = pickle.load(f)
        f.close()
        self.register_file[29][1] = (max(self.memory) + 1) + (1000*4) # Initialise the stack pointer (1000 words).
        self.eu = ExecutionUnit(self.memory, self.register_file)
        self.stdscr = stdscr # Define the curses terminal
        self.setup_screen() # Setup the initial curses layout


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
            self.shutdown()


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
        queue.commit(self.register_file, self.stdscr)


    def simulate(self):
        """
        The main simulate function controlling the:
        fetch, decode, execute and writeback commands.c
        """
        while True:
            # Fetch
            raw_instruction = self.fetch()
            self.clock+=1
            # Decode & Display All
            instruction = self.decode(raw_instruction)
            self.print_state(instruction)
            self.clock+=1
            # Execute
            queue = self.execute(instruction)
            self.clock+=1
            # Retire & Display Updates
            self.retire(queue)
            self.clock+=1


    def print_state(self, instruction):
        """
        This function prints the current state of the simulator to the terminal
        :param instruction: Instruction to be executed.
        """
        self.stdscr.addstr(3, 10, str(instruction.type), curses.color_pair(1))
        self.stdscr.addstr(4, 10, instruction.description(self.register_file).ljust(64), curses.color_pair(1))
        self.stdscr.addstr(9, 10, "Program Counter: " + str(self.pc), curses.color_pair(2))
        self.stdscr.addstr(10, 10, "Clock Cycles Taken: " + str(self.clock), curses.color_pair(3))
        for i in range(34):
            offset = 100
            if i > 20:
                offset += 20
            self.stdscr.addstr(i%20 + 2, offset, str(self.register_file[i][:2]).ljust(16))
        self.stdscr.refresh()


    def setup_screen(self):
        """
        Sets up the curses terminal with the appropriate colour scheme.
        """
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.stdscr.addstr(0, 10, "INSTRUCTION INFORMATION", curses.A_BOLD)
        self.stdscr.addstr(0, 100, "REGISTER FILE", curses.A_BOLD)
        self.stdscr.addstr(7, 10, "MACHINE INFORMATION", curses.A_BOLD)


    def shutdown(self):
        """
        Displays the final values of the return registers and does a memory dump.
        """
        self.stdscr.addstr(24,0, "Memory Dump:", curses.A_BOLD)
        self.stdscr.addstr(25,0, str(self.memory), curses.color_pair(3))
        self.stdscr.addstr(4, 100, str(self.register_file[2][:2]), curses.color_pair(3))
        self.stdscr.addstr(5, 100, str(self.register_file[3][:2]), curses.color_pair(3))
        self.stdscr.refresh()
        exit(0)