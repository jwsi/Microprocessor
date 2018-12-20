import pickle, curses, time
from classes.instruction import Instruction, Type
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile
from classes.constants import debug, instruction_time, N
from classes.errors import Interrupt, AlreadyExecutingInstruction, UnsupportedInstruction
from classes.branch_predictor import BranchPredictor
from classes.reservation_station import ReservationStation
from classes.reorder_buffer import ReOrderBuffer


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
        self.intercept = True
        self.instructions_executed = 0
        self.register_file = RegisterFile()
        self.register_file.reg[29]["value"] = (max(self.memory) + 1) + (1000 * 4)  # Initialise the stack pointer (1000 words).
        # Define some execution units able to execute instructions in a superscalar manner.
        self.master_eu = ExecutionUnit(self.memory, self.register_file)
        self.slave_eu = ExecutionUnit(self.memory, self.register_file, alu=True, lsu=False, beu=False)
        # Define a branch predictor to optimise the global pipeline.
        self.branch_predictor = BranchPredictor()
        # Define a re-order buffer for register renaming and out of order execution.
        self.reorder_buffer = ReOrderBuffer()
        # Define a reservation station to allow for dispatch of instructions.
        self.reservation_station = ReservationStation(self.reorder_buffer)
        self.stdscr = stdscr  # Define the curses terminal
        if not debug:
            self.setup_screen(input_file)  # Setup the initial curses layout


    def simulate(self):
        """
        The main simulate function controlling the:
        fetch, decode, execute and writeback.
        """
        empty_state = [None for _ in range(N)]
        self.raw_instructions = empty_state
        self.prev_raw_instructions = empty_state
        self.exec_results = RegisterFile() # Blank register files.
        self.prev_exec_results = RegisterFile()
        self.now_executing, self.now_writing = [], []
        while True:
            self.clock += 1
            self.advance_pipeline()
            # Check if program is finished.
            finished = self.raw_instructions == empty_state # Nothing fetched
            finished &= self.prev_raw_instructions == empty_state # Nothing to decode
            finished &= len(self.reservation_station.queue) == 0 # Nothing to execute
            finished &= self.reorder_buffer.no_writebacks() # Nothing to writeback
            finished &= not self.branch_predictor.in_recovery
            if finished:
                raise Interrupt()


    def advance_pipeline(self):
        """
        This function will advance the pipeline by one stage.
        :param pipeline: Pipeline to be advanced.
        """
        if not debug:
            self.stdscr.addstr(25+ 3 * (N-1), 10, "Pipeline Status: NORMAL".ljust(64), curses.color_pair(1))  # Clear warnings
        # Check if system has finished recovering from failed branch
        if self.branch_predictor.in_recovery and self.reorder_buffer.no_writebacks():
            self.branch_predictor.in_recovery = False
            self.register_file.set_all_valid()
        # Fetch Stage in Pipeline
        if not self.branch_predictor.in_recovery and len(self.reservation_station.queue) <= 20-N:
            self.raw_instructions = self.fetch()
        # Writeback stage in pipeline
        written_to = self.writeback()
        # Execute Stage in Pipeline
        self.execute()
        # Decode Stage in Pipeline
        if self.prev_raw_instructions != [None for _ in range(N)]:
            self.decode(self.prev_raw_instructions)
        # Do prints and prepare for next round
        if not debug:
            self.print_state(written_to)
        self.prev_raw_instructions, self.raw_instructions = self.raw_instructions, [None for _ in range(N)]
        self.now_writing = [ins for ins in self.now_executing if ins.cycles == 0 and ins.name != "sw"]


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
                    "prediction": prediction,
                    "block" : self.branch_predictor.block
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
                key = self.reorder_buffer.insert_entry(decoded_instruction)
                decoded_instruction.rob_entry = key
                operands = self._get_operands(decoded_instruction)
                decoded_instruction.operands = operands
                self._writeback_analysis(decoded_instruction, key)
                self.reservation_station.add_instruction(decoded_instruction)
            else:
                instructions.append(None)
        return instructions


    def _get_operands(self, ins):
        """
        Given an instruction, this function will calculate the operands required for execution.
        :param ins: Instruction to calculate operands for.
        :return: Dictionary of operands.
        """
        operands = {
            "rs" : {},
            "rt" : {}
        }
        # Type R operands.
        if ins.type == Type.R:
            if ins.name == "jr":
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(ins.rs)
            elif ins.name == "mfhi":
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(32)
                ins.rs = 32
            elif ins.name == "mflo":
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(33)
                ins.rs = 33
            elif ins.name in ["sll", "sra"]:
                operands["rt"]["valid"], operands["rt"]["value"] = self.register_file.get_value(ins.rt)
            else:
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(ins.rs)
                operands["rt"]["valid"], operands["rt"]["value"] = self.register_file.get_value(ins.rt)
        # Type I operands.
        elif ins.type == Type.I and ins.name != "lui":
            if ins.name in ["beq", "bne", "sw"]:
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(ins.rs)
                operands["rt"]["valid"], operands["rt"]["value"] = self.register_file.get_value(ins.rt)
            else:
                operands["rs"]["valid"], operands["rs"]["value"] = self.register_file.get_value(ins.rs)
        return operands


    def _writeback_analysis(self, ins, key):
        """
        Given an instruction and a key this function will rename the architectural register file
        in order to resolve dependencies.
        :param ins: Instruction to inspect.
        :param key: Re-order buffer entry id.
        """
        if ins.type == Type.R:
            if ins.name == "mult":  # Special case for MULT
                self.register_file.invalidate_register(33, key)
            elif ins.name == "div":  # Special case for DIV
                self.register_file.invalidate_register(33, key)
                self.register_file.invalidate_register(32, key)
            elif ins.name == "jr":
                pass
            else:
                self.register_file.invalidate_register(ins.rd, key)
        elif ins.type == Type.I:
            if ins.name in ["beq", "bgtz", "blez", "bne", "sw"]:
                pass
            else:
                self.register_file.invalidate_register(ins.rt, key)
        elif ins.type == Type.J:
            if ins.name == "jal":  # Special case for JAL
                self.register_file.invalidate_register(31, key)


    def execute(self):
        """
        This function executes the Instruction object.
        :param instruction: Instruction object to be executed.
        """
        self.now_executing = []
        instructions = self.reservation_station.get_ready_instructions()
        for instruction in instructions:
            try:
                pc = self.master_eu.execute(instruction, self.reorder_buffer)
            except AlreadyExecutingInstruction:
                try:
                    pc = self.slave_eu.execute(instruction, self.reorder_buffer)
                except (AlreadyExecutingInstruction, UnsupportedInstruction):
                    raise AlreadyExecutingInstruction("Dispatcher Failed...")
            if instruction.cycles == 0:
                self.instructions_executed += 1
            self.now_executing.append(instruction)
            if instruction.name in ["beq", "bne", "blez", "bgtz", "jr"] and pc != instruction.prediction:
                self.branch_predictor.incorrect_predictions += 1
                self.reservation_station.clear_block(instruction.block)
                self.reorder_buffer.clear_block(instruction.block)
                self.branch_predictor.in_recovery = True
                self.branch_predictor.remove_invalid_returns(instruction.block)
                self.flush_pipeline()
                self.pc = pc
                break
        # Free the EU subunits
        self.master_eu.clear_subunits()
        self.slave_eu.clear_subunits()


    def writeback(self):
        """
        This function writes back the pending results from the EUs to the register file.
        :param queue: queue of writebacks.
        :return: List of registers written to in the architectural register file.
        """
        instructions = self.reorder_buffer.get_finished_instructions()
        written_to = []
        for instruction in instructions:
            written_to += self.register_file.write(instruction, self.reorder_buffer)
        return written_to



    def flush_pipeline(self):
        """
        This function flushes a particular pipeline.
        :param pipeline: Pipeline to be flushed.
        """
        if not debug:
            self.stdscr.addstr(25+ 3 * (N-1), 10, "Pipeline Status: BRANCH PREDICTION FAILED - FLUSHING PIPELINE".ljust(64), curses.color_pair(2))
        self.raw_instructions = [None for _ in range(N)] # Clear anything already fetched.
        self.prev_raw_instructions = [None for _ in range(N)] # Clear anything about to be decoded.


    def print_state(self, written_to):
        """
        This function prints the current state of the simulator to the terminal
        :param written_to: List of registers written to in this cycle.
        """
        self.stdscr.addstr(3, 10,
                           "Program Counter: "
                           + str(self.pc),
                           curses.color_pair(2))
        self.stdscr.addstr(4, 10,
                           "Clock Cycles Taken: "
                           + str(self.clock),
                           curses.color_pair(3))
        self.stdscr.addstr(5, 10,
                           "Instructions Per Cycle: "
                           + str(round(self.instructions_executed/self.clock, 2)),
                           curses.color_pair(3))
        self.stdscr.addstr(5, 40,
                           "Instructions Executed: "
                           + str(self.instructions_executed),
                           curses.color_pair(3))
        for i in range(34):
            offset = 100
            if i >= 20:
                offset += 25
            color = 4
            if i in written_to:
                color = 1
            if self.register_file.reg[i]["valid"]:
                valid = "\u2713"
            else:
                valid = "\u002E"
            self.stdscr.addstr(i % 20 + 2, offset,
                               str(self.register_file.reg[i]["name"]) + " v: " +
                               valid + " " +
                               str(self.register_file.reg[i]["value"])[:6] + " rob: " +
                               str(self.register_file.reg[i]["rob_entry"]).ljust(16),
                               curses.color_pair(color))
        for i in range(N):
            try:
                self.stdscr.addstr(14 + i, 10,
                                   "Pipeline Fetch:     "
                                   + str(Instruction(self.raw_instructions[i]).description().ljust(64)),
                                   curses.color_pair(4))
            except:
                self.stdscr.addstr(14 + i, 10,
                                   "Pipeline Fetch:     Empty".ljust(72),
                                   curses.color_pair(4))
            try:
                self.stdscr.addstr(14 + N + i + 1, 10,
                                   "Pipeline Decode:    "
                                   + str(Instruction(self.prev_raw_instructions[i]).description().ljust(64)),
                                   curses.color_pair(1))
            except:
                self.stdscr.addstr(14 + N + i + 1, 10,
                                   "Pipeline Decode:    Empty".ljust(72),
                                   curses.color_pair(1))
            try:
                self.stdscr.addstr(18 + 2*N + i + 3, 10,
                                   "Pipeline Writeback: "
                                   + str(self.now_writing[i].description().ljust(64)),
                                   curses.color_pair(5))
            except:
                self.stdscr.addstr(18 + 2*N + i + 3, 10,
                                   "Pipeline Writeback: Empty".ljust(72),
                                   curses.color_pair(5))
        for i in range(4):
            try:
                self.stdscr.addstr(14 + 2*N + i + 2, 10,
                                   "Pipeline Execute:   "
                                   + str(self.now_executing[i].description().ljust(64)),
                                   curses.color_pair(6))
            except:
                self.stdscr.addstr(14 + 2*N + i + 2, 10,
                                   "Pipeline Execute:   Empty".ljust(72),
                                   curses.color_pair(6))
        self.reservation_station.print(self.stdscr)
        self.branch_predictor.print(self.stdscr)
        self.reorder_buffer.print(self.stdscr)
        self.stdscr.refresh()
        if not self.intercept:
            time.sleep(instruction_time)
        if self.intercept and self.stdscr.getch() == 32:
            self.intercept = False
            self.stdscr.addstr(51, 0, "".ljust(92))


    def setup_screen(self, input_file):
        """
        Sets up the curses terminal with the appropriate colour scheme.
        """
        curses.init_color(curses.COLOR_MAGENTA, 999, 0, 600)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        self.stdscr.addstr(0, 100, "REGISTER FILE", curses.A_BOLD)
        self.stdscr.addstr(0, 10, "MACHINE INFORMATION", curses.A_BOLD)
        self.stdscr.addstr(2, 10, "Program: " + str(input_file), curses.color_pair(4))
        self.stdscr.addstr(4, 35, "Cycles per second: " + str(1 / instruction_time)[:5], curses.color_pair(3))
        self.stdscr.addstr(12, 10, "PIPELINE INFORMATION", curses.A_BOLD)
        self.stdscr.addstr(51, 0, "Press `SPACE' to automate execution or any other key to single step.")


    def shutdown(self):
        """
        Displays the final values of the return registers and does a memory dump.
        """
        self.stdscr.addstr(46, 10, "EXECUTION COMPLETE!", curses.A_BOLD)
        self.stdscr.addstr(47, 10, "1st return value: " + str(self.register_file.reg[2]["value"]), curses.color_pair(3))
        self.stdscr.addstr(48, 10, "2nd return value: " + str(self.register_file.reg[3]["value"]), curses.color_pair(3))
        self.stdscr.addstr(49, 10, "See memory dump at ./memory.out")
        f = open("./memory.out", "wb")
        f.write(str(self.memory).encode('utf-8'))
        f.close()
        self.stdscr.addstr(4, 100,
                           str(self.register_file.reg[2]["name"]) + " v: \u2713 " +
                           str(self.register_file.reg[2]["value"])[:6] + " rob: " +
                           str(self.register_file.reg[2]["rob_entry"]),
                           curses.color_pair(3))
        self.stdscr.addstr(5, 100,
                           str(self.register_file.reg[3]["name"]) + " v: \u2713 " +
                           str(self.register_file.reg[3]["value"])[:6] + " rob: " +
                           str(self.register_file.reg[3]["rob_entry"]),
                           curses.color_pair(3))
        self.stdscr.refresh()
        exit(0)
