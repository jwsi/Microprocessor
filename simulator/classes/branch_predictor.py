from enum import IntEnum
import curses

class BranchPredictor:
    """
    This class serves as the branch predicting system for the simulator (Smith Algorithm).
    """

    class State(IntEnum):
        """
        Potential states of the branch predictor.
        """
        strongly_not_taken = 0
        weakly_not_taken = 1
        weakly_taken = 2
        strongly_taken = 3


    # Define class variables for all instances.
    total_predictions = 1
    incorrect_predictions = 0
    current_state = State.weakly_taken
    return_address_stack = []
    block = 0
    in_recovery = False


    def make_prediction(self, raw_instruction, pc):
        """
        Based on the current state, make a prediction regarding the outcome of the next instruction.
        :return: PC address representing the prediction.
        """
        # If J or JAL the next PC value is known
        if raw_instruction[0:6] in ["000010", "000011"]:
            # If JAL, store the return address on the return address stack.
            if raw_instruction[0:6] == "000011":
                self.block += 1
                self.return_address_stack.append(pc + 4)
            pc = int(raw_instruction[6:32], 2)
        # If JR make a prediction about the return address.
        elif raw_instruction[0:6] == "000000" and raw_instruction[26:32] == "001000":
            try:
                pc = self.return_address_stack.pop()
            except IndexError: # If unable to make a prediction then fall back to next instruction.
                pc += 4
            self.total_predictions += 1
        # If BEQ, BNE, BLEZ or BGTZ work out whether the branch will be taken and update PC accordingly.
        elif raw_instruction[0:6] in ["000100", "000101", "000110", "000111"]:
            if self.current_state in [self.State.weakly_taken, self.State.strongly_taken]:
                pc += 4 * int(raw_instruction[16:32], 2)
            else:
                pc += 4
            self.block += 1
            self.total_predictions += 1
        # For all other instructions increment by 4.
        else:
            pc += 4
        return pc


    @classmethod
    def update_prediction(cls, branch_taken):
        """
        Based on the actual outcome of a branch instruction, update the global predictor state.
        :param branch_taken: Boolean representing whether the branch was actually taken.
        """
        if branch_taken:
            cls.current_state = cls.State(min(cls.current_state + 1, 3))
        else:
            cls.current_state = cls.State(max(cls.current_state - 1, 0))


    def print(self, stdscr):
        """
        Prints the contents of the reservation station to the terminal.
        :param stdscr: terminal to print to.
        """
        stdscr.addstr(7, 10, "BRANCH PREDICTOR".ljust(48), curses.A_BOLD)
        stdscr.addstr(9, 10,
                      "Current State: " +
                      str(self.current_state) +
                      ", Recovery Mode: " +
                      str(self.in_recovery).ljust(24), curses.color_pair(7))
        stdscr.addstr(10, 10,
                      "Branch Prediction Rate: " +
                      str(round(
                          (self.total_predictions - self.incorrect_predictions)
                          / self.total_predictions * 100,
                          2))
                      + "%",
                      curses.color_pair(7))



