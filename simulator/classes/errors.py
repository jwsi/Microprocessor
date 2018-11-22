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