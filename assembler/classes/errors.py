class InvalidLabel(Exception):
    """
    This Exception is raised when an invalid label is specified in assembly.
    """
    pass


class InvalidInstructionName(Exception):
    """
    This Exception is raised when an invalid instruction name is specified in assembly.
    """
    pass


class InvalidInstructionFormat(Exception):
    """
    This Exception is raised when an invalid number of operands are coupled with an assembly instruction.
    """
    pass