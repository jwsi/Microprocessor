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