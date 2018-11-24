import pickle, curses, copy, time
from classes.instruction import Instruction
from classes.execution_unit import ExecutionUnit
from classes.register_file import RegisterFile
from classes.constants import debug, instruction_time
from classes.errors import Interrupt, AlreadyExecutingInstruction, UnsupportedInstruction


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
        # Define a master execution unit able to execute all instructions.
        self.master_eu = ExecutionUnit(self.memory, self.register_file)
        # Define a slave execution unit for ALU and FPU operations.
        self.slave_eu = ExecutionUnit(self.memory, self.register_file, lsu=False, alu=True, beu=False, fpu=True)
        self.stdscr = stdscr # Define the curses terminal
        if not debug:
            self.setup_screen(input_file) # Setup the initial curses layout


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
                    raw_instruction += self.memory[self.pc+offset]
                raw_instructions.append({
                    "pc" : self.pc,
                    "raw_instruction" : raw_instruction
                })
            except KeyError:
                raw_instructions.append(None)
            finally:
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
                instructions.append(Instruction(instruction["pc"], instruction["raw_instruction"]))
            else:
                instructions.append(None)
        return instructions


    def execute(self, pipeline):
        """
        This function executes the Instruction object.
        :param instruction: Instruction object to be executed.
        """
        queues = [None, None]
        interrupt = False
        for i in range(2):
            if pipeline[self.clock - 1]["decode"][i] is None: # Cannot execute an instruction that doesn't exist.
                continue
            try:
                pc, queues[i] = self.master_eu.execute(pipeline[self.clock - 1]["decode"][i])
            except AlreadyExecutingInstruction:
                try:
                    pc, queues[i] = self.slave_eu.execute(pipeline[self.clock - 1]["decode"][i])
                except (AlreadyExecutingInstruction, UnsupportedInstruction):
                    pass
                    # STALL THE PIPE
            except Interrupt:  # Catch Interrupts and flag them for raising.
                interrupt = True
                continue

            if pc != pipeline[self.clock - 1]["decode"][i].pc + 4:
                self.flush_pipeline(pipeline)
                self.pc = pc
                break
        # Free the EU subunits
        self.master_eu.clear_subunits()
        self.slave_eu.clear_subunits()
        return queues, interrupt


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
            "fetch" : [None, None],
            "decode" : [None, None],
            "execute" : [None, None]
        }
        pipeline = [copy.copy(stages)]
        interrupt = False
        while True:
            self.clock += 1
            # self.dependency_check(pipeline)
            pipeline.append(copy.copy(stages))
            interrupt = self.advance_pipeline(pipeline, interrupt)


    def advance_pipeline(self, pipeline, interrupt):
        """
        This function will advance the pipeline by one stage.
        :param pipeline: Pipeline to be advanced.
        """
        last_run = interrupt
        if not debug:
            self.stdscr.addstr(13, 10, "".ljust(64), curses.color_pair(2)) # Clear warnings
        # Fetch Stage in Pipeline
        if not interrupt:
            pipeline[self.clock]["fetch"] = self.fetch()
        # Decode Stage in Pipeline & Display All
        if not interrupt and pipeline[self.clock - 1]["fetch"] is not [None, None]:
            pipeline[self.clock]["decode"] = self.decode(pipeline[self.clock - 1]["fetch"])
        # Execute Stage in Pipeline
        if not interrupt and pipeline[self.clock - 1]["decode"] is not [None, None]:
            pipeline[self.clock]["execute"], interrupt = self.execute(pipeline)
        # Writeback stage in pipeline
        if not debug:
            self.print_state(pipeline)
        if pipeline[self.clock - 1]["execute"] is not [None, None]:
            self.writeback(pipeline[self.clock - 1]["execute"])
        if last_run: # If there was an interrupt. Writeback last execution results and raise.
            raise Interrupt()
        return interrupt


    def dependency_check(self, pipeline):
        """
        This function analyses instructions in the pipeline for dependencies.
        If there are dependencies, the pipeline is stalled for one cycle.
        :param pipeline: Pipeline to analyse.
        """
        if pipeline[self.clock-1]["execute"] is not None and pipeline[self.clock-1]["decode"] is not None:
            writeback_dependency = pipeline[self.clock-1]["execute"].get_dependencies()
            execute_dependency = [pipeline[self.clock-1]["decode"].rs]
            execute_dependency.append(pipeline[self.clock-1]["decode"].rt)
            execute_dependency.append(pipeline[self.clock - 1]["decode"].rd)
            # Add hi/low registers for mult/div operations.
            if pipeline[self.clock - 1]["decode"].name in ["mult", "mflo"]:
                execute_dependency.append(33)
            elif pipeline[self.clock - 1]["decode"].name is "div":
                execute_dependency.append(32, 33)
            elif pipeline[self.clock - 1]["decode"].name is "mfhi":
                execute_dependency.append(33)
            if bool(set(writeback_dependency) & set(execute_dependency)):
                # If there are dependencies sort them out by writing back first then executing next.
                pipeline.append(copy.copy(pipeline[self.clock-1]))
                pipeline[self.clock-1]["decode"] = None
                pipeline[self.clock]["execute"] = None
                if not debug:
                    self.stdscr.addstr(13, 10, "MEMORY RACE - STALLING NOW", curses.color_pair(2))
                    self.print_state(pipeline)
                self.writeback(pipeline[self.clock - 1]["execute"])
                self.clock += 1


    def flush_pipeline(self, pipeline):
        """
        This function flushes a particular pipeline.
        :param pipeline: Pipeline to be flushed.
        """
        self.stdscr.addstr(13, 10, "BRANCH PREDICTION FAILED - FLUSHING PIPELINE", curses.color_pair(2))
        pipeline[self.clock]["fetch"] = None
        pipeline[self.clock]["decode"] = None


    def print_state(self, pipeline):
        """
        This function prints the current state of the simulator to the terminal
        :param instruction: Instruction to be executed.
        """
        sleep = 0
        self.stdscr.addstr(3, 10, "Program Counter: " + str(self.pc), curses.color_pair(2))
        self.stdscr.addstr(4, 10, "Clock Cycles Taken: " + str(self.clock), curses.color_pair(3))
        for i in range(34):
            offset = 100
            if i > 20:
                offset += 20
            self.stdscr.addstr(i%20 + 2, offset, str(self.register_file[i][:2]).ljust(16))
        for i in range(2):
            try:
                self.stdscr.addstr(8+i, 10, "Pipeline Fetch:     " + str(self.decode(pipeline[self.clock]["fetch"])[i].description(self.register_file).ljust(64)), curses.color_pair(4))
            except:
                self.stdscr.addstr(8+i, 10, "Pipeline Fetch:     Empty".ljust(72), curses.color_pair(4))
            try:
                self.stdscr.addstr(10+i, 10, "Pipeline Decode:    " + str(pipeline[self.clock]["decode"][i].description(self.register_file).ljust(64)), curses.color_pair(1))
            except:
                self.stdscr.addstr(10+i, 10, "Pipeline Decode:    Empty".ljust(72), curses.color_pair(1))
            try:
                self.stdscr.addstr(12+i, 10, "Pipeline Execute:   " + str(pipeline[self.clock-1]["decode"][i].description(self.register_file).ljust(64)), curses.color_pair(6))
            except:
                self.stdscr.addstr(12+i, 10, "Pipeline Execute:   Empty".ljust(72), curses.color_pair(6))
            try:
                self.stdscr.addstr(14+i, 10, "Pipeline Writeback: " + str(pipeline[self.clock-2]["decode"][i].description(self.register_file).ljust(64)), curses.color_pair(5))
            except:
                self.stdscr.addstr(14+i, 10, "Pipeline Writeback: Empty".ljust(72), curses.color_pair(5))
                sleep += 1
        self.stdscr.refresh()
        if sleep == 2:
            time.sleep(instruction_time) # Need to account for no writeback pause.


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
        self.stdscr.addstr(4, 35, "Cycles per second: " + str(1/instruction_time)[:5], curses.color_pair(3))
        self.stdscr.addstr(6, 10, "PIPELINE INFORMATION", curses.A_BOLD)


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