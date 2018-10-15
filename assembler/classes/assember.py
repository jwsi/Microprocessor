class Assembler():
    """
    This class is the main assembler class defining all operations.
    """
    # Define input and output file
    input_file = None
    output_file = None

    # Define memory dictionary which will be dumped into machine code.
    memory = dict()

    def __init__(self, input_file, output_file):
        """
        Constructor for the Assembler class.
        :param input_file: input source assembly file.
        :param output_file: output file to write to (or stdout if None)
        """
        self.input_file = input_file
        self.output_file = output_file


    def output(self):
        """
        Outputs calculated machine code to the requested destination.
        """
        if self.output_file is None:
            print("assembly")
        else:
            f = open(self.output_file, 'w')
            f.write("assembly")
            f.close()



