import pickle, curses, copy, time
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile
from classes.constants import debug, instruction_time


class Simulator():
    """
    This is the class for the main processor simulator.
    """
    memory = None
    pc = None
    clock = 0
    register_file = RegisterFile().reg # Create the parent register file for the simulator
    strikes = 0

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
        if not debug:
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
            self.pc += 4
            return self.pc - 4, raw_instruction
        except KeyError:
            return None


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
        pc, queue = self.eu.execute(instruction[0], instruction[1])
        return pc, queue


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
        stages = {
            "fetch" : None, # Default to no-op
            "decode" : None,
            "execute" : None,
        }
        pipeline = [copy.copy(stages)]
        while True:
            self.clock += 1
            pipeline.append(copy.copy(stages))
            # Fetch Stage in Pipeline
            pipeline[self.clock]["fetch"] = self.fetch()
            # Decode Stage in Pipeline & Display All
            if pipeline[self.clock - 1]["fetch"] is not None:
                pipeline[self.clock]["decode"] = pipeline[self.clock - 1]["fetch"][0], self.decode(pipeline[self.clock - 1]["fetch"][1])
            # Execute Stage in Pipeline
            if pipeline[self.clock - 1]["decode"] is not None:
                pc, pipeline[self.clock]["execute"] = self.execute(pipeline[self.clock - 1]["decode"])
                if pc != self.pc - 8:
                    self.flush(pipeline)
                    self.pc = pc
            # Retire Stage in Pipeline & Show updates.
            if pipeline[self.clock - 1]["execute"] is not None:
                self.retire(pipeline[self.clock - 1]["execute"])
            if not debug:
                self.print_state(pipeline)


    def flush(self, pipeline):
        pipeline[self.clock]["fetch"] = None
        pipeline[self.clock]["decode"] = None


    def print_state(self, pipeline):
        """
        This function prints the current state of the simulator to the terminal
        :param instruction: Instruction to be executed.
        """
        self.stdscr.addstr(2, 10, "Program Counter: " + str(self.pc), curses.color_pair(2))
        self.stdscr.addstr(3, 10, "Clock Cycles Taken: " + str(self.clock), curses.color_pair(3))
        for i in range(34):
            offset = 100
            if i > 20:
                offset += 20
            self.stdscr.addstr(i%20 + 2, offset, str(self.register_file[i][:2]).ljust(16))
        try:
            self.stdscr.addstr(7, 10, "Pipeline Fetch:     " + str(self.decode(pipeline[self.clock]["fetch"][1]).description(self.register_file).ljust(64)), curses.color_pair(4))
        except:
            self.stdscr.addstr(7, 10, "Pipeline Fetch:     Empty".ljust(64), curses.color_pair(4))
        try:
            self.stdscr.addstr(8, 10, "Pipeline Decode:    " + str(pipeline[self.clock]["decode"][1].description(self.register_file).ljust(64)), curses.color_pair(1))
        except:
            self.stdscr.addstr(8, 10, "Pipeline Decode:    Empty".ljust(64), curses.color_pair(1))
        try:
            self.stdscr.addstr(9, 10, "Pipeline Execute:   " + str(pipeline[self.clock-1]["decode"][1].description(self.register_file).ljust(64)), curses.color_pair(6))
        except:
            self.stdscr.addstr(9, 10, "Pipeline Execute:   Empty".ljust(64), curses.color_pair(6))
        try:
            self.stdscr.addstr(10, 10, "Pipeline Writeback: " + str(pipeline[self.clock-2]["decode"][1].description(self.register_file).ljust(64)), curses.color_pair(5))
        except:
            self.stdscr.addstr(10, 10, "Pipeline Writeback: Empty".ljust(64), curses.color_pair(5))
            time.sleep(instruction_time) # Need to account for no writeback pause.
        self.stdscr.refresh()


    def setup_screen(self):
        """
        Sets up the curses terminal with the appropriate colour scheme.
        """
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        self.stdscr.addstr(0, 100, "REGISTER FILE", curses.A_BOLD)
        self.stdscr.addstr(0, 10, "MACHINE INFORMATION", curses.A_BOLD)
        self.stdscr.addstr(5, 10, "PIPELINE INFORMATION", curses.A_BOLD)


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