class InvalidOpcode(Exception):
    """
    This Exception is raised when an invalid opcode is decoded.
    """
    pass


class Interrupt(Exception):
    """
    This Exception is raised when a syscall is used.
    """
    pass


class UnsupportedInstruction(Exception):
    """
    This Exception is raised when an instruction is sent to an execution unit without the necessary capabilities.
    """
    pass


class AlreadyExecutingInstruction(Exception):
    """
    This Exception is raised when a subunit of an execution unit is already busy trying to execute an instruction.
    """
    pass


class ResultNotReady(Exception):
    """
    This Exception is raised when a result is asked for in a ROB entry that is not yet ready.
    """
    pass