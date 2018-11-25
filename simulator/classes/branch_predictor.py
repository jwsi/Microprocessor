from enum import IntEnum

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

    current_state = State.weakly_taken


    def make_prediction(self):
        """
        Based on the current state, make a prediction regarding the outcome of the next branch instruction.
        :return: Boolean representing whether the branch should be taken.
        """
        if self.current_state in [self.State.wt, self.State.st]:
            return True
        return False


    @classmethod
    def update_prediction(cls, branch_taken):
        """
        Based on the actual outcome of a branch instruction, update the global predictor state.
        :param branch_taken: Boolean representing whether the branch was actually taken.
        """
        if branch_taken:
            cls.current_state = min(cls.current_state + 1, 3)
        else:
            cls.current_state = max(cls.current_state - 1, 0)


