import pickle, curses, copy, time
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile
from classes.constants import debug, instruction_time
from classes.errors import Interrupt, AlreadyExecutingInstruction, UnsupportedInstruction
from classes.branch_predictor import BranchPredictor


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
        # Set the internal clock and define a global register file.
        self.clock = 0
        self.register_file = RegisterFile().reg
        self.register_file[29][1] = (max(self.memory) + 1) + (1000 * 4)  # Initialise the stack pointer (1000 words).
        # Define some execution units able to execute instructions in a superscalar manner.
        self.master_eu = ExecutionUnit(self.memory, self.register_file)
        self.slave_eu = ExecutionUnit(self.memory, self.register_file, alu=True, lsu=False, beu=False)
        # Define a branch predictor to optimise the global pipeline.
        self.branch_predictor = BranchPredictor()
        self.stdscr = stdscr  # Define the curses terminal
        if not debug:
            self.setup_screen(input_file)  # Setup the initial curses layout


    def fetch(self):
        """
        This function fetches the appropriate instruction from memory.
        :return: raw binary instruction (string).
        """
        raw_instructions = []
        for i in range(2):
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
                instructions.append(Instruction(instruction))
            else:
                instructions.append(None)
        return instructions


    def execute(self, pipeline):
        """
        This function executes the Instruction object.
        :param instruction: Instruction object to be executed.
        """
        queues = [None, None]
        for i in range(2):
            instruction = pipeline[self.clock - 1]["decode"][i]
            if instruction is None:  # Cannot execute an instruction that doesn't exist.
                continue
            try:
                pc, queues[i] = self.master_eu.execute(instruction)
            except AlreadyExecutingInstruction:
                try:
                    pc, queues[i] = self.slave_eu.execute(instruction)
                except (AlreadyExecutingInstruction, UnsupportedInstruction):
                    raise AlreadyExecutingInstruction("Dispatcher Failed...")
            if instruction.name in ["beq", "bne", "blez", "bgtz", "jr"] and pc != instruction.prediction:
                self.branch_predictor.incorrect_predictions += 1
                self.flush_pipeline(pipeline)
                self.pc = pc
                break
        # Free the EU subunits
        self.master_eu.clear_subunits()
        self.slave_eu.clear_subunits()
        return queues


    def writeback(self, queues):
        """
        This function writes back the pending results from the EUs to the register file.
        :param queue: queue of writebacks.
        """
        sleep = False
        for queue in queues:
            if queue is not None:
                sleep = True
                queue.commit(self.register_file, self.stdscr)
        if sleep and not debug:
            time.sleep(instruction_time)


    def simulate(self):
        """
        The main simulate function controlling the:
        fetch, decode, execute and writeback.
        """
        stages = {
            "fetch": [None, None],
            "decode": [None, None],
            "execute": [None, None]
        }
        pipeline = [copy.copy(stages)]
        while True:
            self.clock += 1
            while self.writeback_dependency_check(pipeline):
                pass
            self.inter_instruction_depenedency_check(pipeline)
            pipeline.append(copy.copy(stages))
            self.advance_pipeline(pipeline)
            # Check if program is finished.
            if pipeline[self.clock] == stages:
                raise Interrupt()


    def advance_pipeline(self, pipeline):
        """
        This function will advance the pipeline by one stage.
        :param pipeline: Pipeline to be advanced.
        """
        if not debug:
            self.stdscr.addstr(18, 10, "".ljust(64), curses.color_pair(2))  # Clear warnings
        # Fetch Stage in Pipeline
        pipeline[self.clock]["fetch"] = self.fetch()
        # Decode Stage in Pipeline & Display All
        if pipeline[self.clock - 1]["fetch"] is not [None, None]:
            pipeline[self.clock]["decode"] = self.decode(pipeline[self.clock - 1]["fetch"])
        # Execute Stage in Pipeline
        if pipeline[self.clock - 1]["decode"] is not [None, None]:
            pipeline[self.clock]["execute"] = self.execute(pipeline)
        # Writeback stage in pipeline
        if not debug:
            self.print_state(pipeline)
        if pipeline[self.clock - 1]["execute"] is not [None, None]:
            self.writeback(pipeline[self.clock - 1]["execute"])


    def writeback_dependency_check(self, pipeline):
        """
        This function analyses instructions in the pipeline for dependencies.
        If there are dependencies, the pipeline is stalled for one cycle.
        :param pipeline: Pipeline to analyse.
        """
        writeback_dependency, execute_dependency, dependant_instructions = [], [[], []], []
        for i in range(2):  # Add writeback dependencies
            if pipeline[self.clock - 1]["execute"][i] is not None:
                writeback_dependency += pipeline[self.clock - 1]["execute"][i].get_dependencies()
        for i in range(2):  # Add execute dependencies
            if pipeline[self.clock - 1]["decode"][i] is not None:
                execute_dependency[i].append(pipeline[self.clock - 1]["decode"][i].rs)
                execute_dependency[i].append(pipeline[self.clock - 1]["decode"][i].rt)
                execute_dependency[i].append(pipeline[self.clock - 1]["decode"][i].rd)
                # Add hi/low registers for mult/div operations.
                if pipeline[self.clock - 1]["decode"][i].name in ["mult", "mflo"]:
                    execute_dependency[i].append(33)
                elif pipeline[self.clock - 1]["decode"][i].name is "div":
                    execute_dependency[i].append(32, 33)
                elif pipeline[self.clock - 1]["decode"][i].name is "mfhi":
                    execute_dependency[i].append(33)
                if bool(set(writeback_dependency) & set(execute_dependency[i])):
                    dependant_instructions.append(i)
        if dependant_instructions:  # If dependent instructions exist, stall the pipe.
            self.stall_pipeline(pipeline, dependant_instructions)
            return True
        return False


    def inter_instruction_depenedency_check(self, pipeline):
        """
        If two instructions have dependencies, this function will execute them separately.
        :param pipeline: Pipeline to inspect.
        """
        instructions = pipeline[self.clock - 1]["decode"]
        registers = [[], []]
        if None not in instructions:  # No dependencies if only one instruction is executed.
            for i in range(2):
                registers[i].append(instructions[i].rs)
                registers[i].append(instructions[i].rt)
                registers[i].append(instructions[i].rd)
                if instructions[i].name in ["mult", "div", "mflo"]:
                    registers[i].append(33)
                if instructions[i].name in ["div", "mfhi"]:
                    registers[i].append(32)
                if instructions[i].name in ["jal"]:
                    registers[i].append(31)
                registers[i] = [reg for reg in registers[i] if
                                reg is not None and reg != 0]  # Remove false dependencies
        if bool(set(registers[0]) & set(registers[1])) or self.hardware_limitation_check(instructions):
            pipeline.append(copy.deepcopy(pipeline[self.clock - 1]))
            pipeline[self.clock - 1]["decode"][1] = None
            pipeline[self.clock]["decode"][0] = None
            pipeline[self.clock]["execute"] = self.execute(pipeline)
            if not debug:
                self.stdscr.addstr(18, 10, "INTER INSTRUCTION DEPENDENCY - SEPARATING NOW".ljust(64),
                                   curses.color_pair(2))
                self.print_state(pipeline)
            if pipeline[self.clock - 1]["execute"] is not [None, None]:
                self.writeback(pipeline[self.clock - 1]["execute"])
            self.clock += 1
            if bool(set(registers[0]) & set(registers[1])):
                self.stall_pipeline(pipeline, [1])  # Writeback 0th instruction first if there is a memory race.

    def hardware_limitation_check(self, instructions):
        """
        Given a list of instructions this function will determine if they can be executed concurrently.
        This is based on hardware availability such as ALUs available etc...
        :param instructions: List of instructions to inspect.
        :return: Boolean representing whether the instructions should be separated.
        """
        lsu_list = ["lw", "sw"]
        beu_list = ["beq", "bne", "blez", "bgtz", "j", "jal", "jr"]
        lsu_instructions, beu_instructions = 0, 0
        if None in instructions:
            return False
        for i in range(2):
            if instructions[i].name in lsu_list:
                lsu_instructions += 1
            elif instructions[i].name in beu_list:
                beu_instructions += 1
        if lsu_instructions > 1 or beu_instructions > 1:
            return True
        return False

    def stall_pipeline(self, pipeline, dependent_instructions):
        """
        Stalls the pipeline if there are dependent instructions queued.
        :param pipeline: Pipeline to stall.
        :param dependent_instructions: list of dependent instruction numbers.
        """
        # If there are dependencies sort them out by writing back first then executing next.
        pipeline.append(copy.deepcopy(pipeline[self.clock - 1]))
        for instruction_number in dependent_instructions:
            pipeline[self.clock - 1]["decode"][instruction_number] = None
            if len(dependent_instructions) == 1:
                pipeline[self.clock]["decode"][(instruction_number + 1) % 2] = None
            pipeline[self.clock]["execute"][instruction_number] = None
        pipeline[self.clock]["execute"] = self.execute(pipeline)
        if not debug:
            self.stdscr.addstr(18, 10, "MEMORY RACE - STALLING NOW".ljust(64), curses.color_pair(2))
            self.print_state(pipeline)
        self.writeback(pipeline[self.clock - 1]["execute"])
        self.clock += 1

    def flush_pipeline(self, pipeline):
        """
        This function flushes a particular pipeline.
        :param pipeline: Pipeline to be flushed.
        """
        if not debug:
            self.stdscr.addstr(18, 10, "BRANCH PREDICTION FAILED - FLUSHING PIPELINE".ljust(64), curses.color_pair(2))
        pipeline[self.clock]["fetch"] = [None, None]
        pipeline[self.clock]["decode"] = [None, None]

    def print_state(self, pipeline):
        """
        This function prints the current state of the simulator to the terminal
        :param instruction: Instruction to be executed.
        """
        sleep = 0
        self.stdscr.addstr(3, 10, "Program Counter: " + str(self.pc), curses.color_pair(2))
        self.stdscr.addstr(4, 10, "Clock Cycles Taken: " + str(self.clock), curses.color_pair(3))
        self.stdscr.addstr(5, 10, "Branch Prediction Rate: " +
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
        for i in range(2):
            try:
                self.stdscr.addstr(9 + i, 10, "Pipeline Fetch:     " + str(
                    self.decode(pipeline[self.clock]["fetch"])[i].description(self.register_file).ljust(64)),
                                   curses.color_pair(4))
            except:
                self.stdscr.addstr(9 + i, 10, "Pipeline Fetch:     Empty".ljust(72), curses.color_pair(4))
            try:
                self.stdscr.addstr(11 + i, 10, "Pipeline Decode:    " + str(
                    pipeline[self.clock]["decode"][i].description(self.register_file).ljust(64)), curses.color_pair(1))
            except:
                self.stdscr.addstr(11 + i, 10, "Pipeline Decode:    Empty".ljust(72), curses.color_pair(1))
            try:
                self.stdscr.addstr(13 + i, 10, "Pipeline Execute:   " + str(
                    pipeline[self.clock - 1]["decode"][i].description(self.register_file).ljust(64)),
                                   curses.color_pair(6))
            except:
                self.stdscr.addstr(13 + i, 10, "Pipeline Execute:   Empty".ljust(72), curses.color_pair(6))
            try:
                self.stdscr.addstr(15 + i, 10, "Pipeline Writeback: " + str(
                    pipeline[self.clock - 2]["decode"][i].description(self.register_file).ljust(64)),
                                   curses.color_pair(5))
            except:
                self.stdscr.addstr(15 + i, 10, "Pipeline Writeback: Empty".ljust(72), curses.color_pair(5))
                sleep += 1
        self.stdscr.refresh()
        if sleep == 2:
            time.sleep(instruction_time)  # Need to account for no writeback pause.

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
        self.stdscr.addstr(24, 0, "Memory Dump:", curses.A_BOLD)
        self.stdscr.addstr(25, 0, str(self.memory), curses.color_pair(3))
        self.stdscr.addstr(4, 100, str(self.register_file[2][:2]), curses.color_pair(3))
        self.stdscr.addstr(5, 100, str(self.register_file[3][:2]), curses.color_pair(3))
        self.stdscr.refresh()
        exit(0)
