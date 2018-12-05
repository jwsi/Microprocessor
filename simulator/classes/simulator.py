import pickle, curses, copy, time
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile
from classes.constants import debug, instruction_time
from classes.errors import Interrupt, AlreadyExecutingInstruction, UnsupportedInstruction
from classes.branch_predictor import BranchPredictor
from classes.reservation_station import ReservationStation

N = 4 # Define N to represent an n-way superscalar design.

class Simulator():
    """
    This is the class for the main processor simulator.
    """

    def __init__(self, input_file, stdscr):
        """
        Constructor for the Simulator class.
        :param input_file: input source machine code file.
        """
        # Re-construct the binary file and parse it.
        f = open(input_file, "rb")
        self.memory = pickle.load(f)
        self.pc = pickle.load(f)
        f.close()
        # Set the internal clock, total number of instructions executed and define a global register file.
        self.clock = 0
        self.instructions_executed = 0
        self.register_file = RegisterFile().reg
        self.register_file[29][1] = (max(self.memory) + 1) + (1000 * 4)  # Initialise the stack pointer (1000 words).
        # Define some execution units able to execute instructions in a superscalar manner.
        self.master_eu = ExecutionUnit(self.memory, self.register_file)
        self.slave_eu = ExecutionUnit(self.memory, self.register_file, alu=True, lsu=False, beu=False)
        # Define a branch predictor to optimise the global pipeline.
        self.branch_predictor = BranchPredictor()
        # Define a reservation station to allow for dispatch of instructions
        self.reservation_station = ReservationStation()
        self.stdscr = stdscr  # Define the curses terminal
        if not debug:
            self.setup_screen(input_file)  # Setup the initial curses layout


    def fetch(self):
        """
        This function fetches the appropriate instruction from memory.
        :return: raw binary instruction (string).
        """
        raw_instructions = []
        for i in range(N):
            try:
                raw_instruction = ""
                for offset in range(4):
                    raw_instruction += self.memory[self.pc + offset]
                prediction = self.branch_predictor.make_prediction(raw_instruction, self.pc)
                raw_instructions.append({
                    "pc": self.pc,
                    "raw_instruction": raw_instruction,
                    "prediction": prediction
                })
                self.pc = prediction
            except KeyError:
                raw_instructions.append(None)
                self.pc += 4
        return raw_instructions


    def decode(self, fetch_object):
        """
        This function decodes the raw instruction into a Instruction object.
        :param raw_instruction: binary string of MIPS instruction.
        :return: Instruction object.
        """
        instructions = []
        for instruction in fetch_object:
            if instruction is not None:
                decoded_instruction = Instruction(instruction)
                instructions.append(decoded_instruction)
                self.reservation_station.add_instruction(decoded_instruction)
            else:
                instructions.append(None)
        return instructions


    def execute(self, pipeline, bypass):
        """
        This function executes the Instruction object.
        :param instruction: Instruction object to be executed.
        """
        queue = RegisterFile()
        instructions = self.reservation_station.get_ready_instructions()
        for instruction in instructions:
            try:
                pc = self.master_eu.execute(instruction, bypass, queue)
            except AlreadyExecutingInstruction:
                try:
                    pc = self.slave_eu.execute(instruction, bypass, queue)
                except (AlreadyExecutingInstruction, UnsupportedInstruction):
                    raise AlreadyExecutingInstruction("Dispatcher Failed...")
            self.instructions_executed += 1
            if instruction.name in ["beq", "bne", "blez", "bgtz", "jr"] and pc != instruction.prediction:
                self.branch_predictor.incorrect_predictions += 1
                self.reservation_station.clear()
                self.flush_pipeline(pipeline)
                self.pc = pc
                break
        # Free the EU subunits
        self.master_eu.clear_subunits()
        self.slave_eu.clear_subunits()
        return queue


    def writeback(self, queue):
        """
        This function writes back the pending results from the EUs to the register file.
        :param queue: queue of writebacks.
        """
        queue.commit(self.register_file, self.stdscr)


    def simulate(self):
        """
        The main simulate function controlling the:
        fetch, decode, execute and writeback.
        """
        stages = {
            "fetch": [None for _ in range(N)],
            "decode": [None for _ in range(N)],
            "execute": None
        }
        pipeline = [copy.copy(stages)]
        while True:
            self.clock += 1
            pipeline.append(copy.copy(stages))
            self.advance_pipeline(pipeline)
            # Check if program is finished.
            if pipeline[self.clock]["fetch"]  == stages["fetch"]  and \
               pipeline[self.clock]["decode"] == stages["decode"] and \
               len(self.reservation_station.queue) == 0           and \
               pipeline[self.clock]["execute"].no_writebacks():
                raise Interrupt()


    def advance_pipeline(self, pipeline):
        """
        This function will advance the pipeline by one stage.
        :param pipeline: Pipeline to be advanced.
        """
        if not debug:
            self.stdscr.addstr(26, 10, "".ljust(64), curses.color_pair(2))  # Clear warnings
        # Fetch Stage in Pipeline
        if len(self.reservation_station.queue) <= 12:
            pipeline[self.clock]["fetch"] = self.fetch()
        # Execute Stage in Pipeline
        pipeline[self.clock]["execute"] = self.execute(pipeline, pipeline[self.clock - 1]["execute"])
        # Decode Stage in Pipeline & Display All
        if pipeline[self.clock - 1]["fetch"] != [None for _ in range(N)]:
            self.decode(pipeline[self.clock - 1]["fetch"])
        # Writeback stage in pipeline
        if pipeline[self.clock - 1]["execute"] is not None:
            self.writeback(pipeline[self.clock - 1]["execute"])
        if not debug:
            self.print_state(pipeline)


    def flush_pipeline(self, pipeline):
        """
        This function flushes a particular pipeline.
        :param pipeline: Pipeline to be flushed.
        """
        if not debug:
            self.stdscr.addstr(26, 10, "BRANCH PREDICTION FAILED - FLUSHING PIPELINE".ljust(64), curses.color_pair(2))
        pipeline[self.clock]["fetch"] = [None, None, None, None] # Clear anything already fetched.
        pipeline[self.clock-1]["fetch"] = [None, None, None, None] # Clear anything about to be decoded.
        pipeline[self.clock]["decode"] = [None, None, None, None] # Clear anything decoded already.


    def print_state(self, pipeline):
        """
        This function prints the current state of the simulator to the terminal
        :param instruction: Instruction to be executed.
        """
        sleep = 0
        self.stdscr.addstr(3, 10, "Program Counter: " + str(self.pc), curses.color_pair(2))
        self.stdscr.addstr(4, 10, "Clock Cycles Taken: " + str(self.clock), curses.color_pair(3))
        self.stdscr.addstr(5, 10, "Instructions Per Cycle: " + str(round(self.instructions_executed/self.clock, 2)), curses.color_pair(3))
        self.stdscr.addstr(6, 10, "Branch Prediction Rate: " +
                           str(
                               round((
                                                 self.branch_predictor.total_predictions - self.branch_predictor.incorrect_predictions) / self.branch_predictor.total_predictions * 100,
                                     2))
                           + "%")
        for i in range(34):
            offset = 100
            if i > 20:
                offset += 20
            self.stdscr.addstr(i % 20 + 2, offset, str(self.register_file[i][:2]).ljust(16))
        for i in range(4):
            try:
                self.stdscr.addstr(9 + i, 10, "Pipeline Fetch:     " + str(
                    Instruction(pipeline[self.clock]["fetch"][i]).description().ljust(64)),
                                   curses.color_pair(4))
            except:
                self.stdscr.addstr(9 + i, 10, "Pipeline Fetch:     Empty".ljust(72), curses.color_pair(4))
            try:
                self.stdscr.addstr(13 + i, 10, "Pipeline Decode:    " + str(
                    pipeline[self.clock]["decode"][i].description().ljust(64)), curses.color_pair(1))
            except:
                self.stdscr.addstr(13 + i, 10, "Pipeline Decode:    Empty".ljust(72), curses.color_pair(1))
            try:
                self.stdscr.addstr(17 + i, 10, "Pipeline Execute:   " + str(
                    self.executing[i].description().ljust(64)),
                                   curses.color_pair(6))
            except:
                self.stdscr.addstr(17 + i, 10, "Pipeline Execute:   Empty".ljust(72), curses.color_pair(6))
            try:
                self.stdscr.addstr(21 + i, 10, "Pipeline Writeback: " + str(
                    self.writing_back[i].description().ljust(64)),
                                   curses.color_pair(5))
            except:
                self.stdscr.addstr(21 + i, 10, "Pipeline Writeback: Empty".ljust(72), curses.color_pair(5))
                sleep += 1
        self.reservation_station.print(self.stdscr)
        self.stdscr.refresh()

    def setup_screen(self, input_file):
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
        self.stdscr.addstr(2, 10, "Program: " + str(input_file), curses.color_pair(4))
        self.stdscr.addstr(4, 35, "Cycles per second: " + str(1 / instruction_time)[:5], curses.color_pair(3))
        self.stdscr.addstr(7, 10, "PIPELINE INFORMATION", curses.A_BOLD)

    def shutdown(self):
        """
        Displays the final values of the return registers and does a memory dump.
        """
        self.stdscr.addstr(26, 0, "Memory Dump:", curses.A_BOLD)
        self.stdscr.addstr(27, 0, str(self.memory), curses.color_pair(3))
        self.stdscr.addstr(4, 100, str(self.register_file[2][:2]), curses.color_pair(3))
        self.stdscr.addstr(5, 100, str(self.register_file[3][:2]), curses.color_pair(3))
        self.stdscr.refresh()
        exit(0)
