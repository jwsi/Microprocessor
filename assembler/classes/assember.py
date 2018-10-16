class Assembler():
    """
    This class is the main assembler class defining all operations.
    """
    # Define input and output file
    assembly = None
    output_file = None

    # Define memory dictionary which will be dumped into machine code.
    next_address = 0
    memory = dict()
    labels = dict()

    def __init__(self, input_file, output_file):
        """
        Constructor for the Assembler class.
        :param input_file: input source assembly file.
        :param output_file: output file to write to (or stdout if None)
        """
        f = open(input_file, "r")
        self.assembly = f.read()
        f.close()
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


    def insert_data(self, label, operand):
        type = operand.split(" ")[0]

        if type == ".word":
            self.labels[label] = self.next_address
            parameters = operand.split(".word")[1].split(",")
            for parameter in parameters:
                parameter = int(parameter.strip())
                hex = parameter.to_bytes(4, byteorder="little", signed=True).hex()
                self.memory[self.next_address  ] = "{0:08b}".format(int(hex[0:2], 16))
                self.memory[self.next_address+1] = "{0:08b}".format(int(hex[2:4], 16))
                self.memory[self.next_address+2] = "{0:08b}".format(int(hex[4:6], 16))
                self.memory[self.next_address+3] = "{0:08b}".format(int(hex[6:8], 16))
                self.next_address += 4


    def build_data(self, data_segment):
        for line in data_segment:
            try:
                label, operand = line.split(":")[0], line.split(":")[1].strip()
            except:
                # Skip invalid lines
                continue
            self.insert_data(label, operand)



    def first_pass(self):
        data_segment = self.assembly.split(".data")[1].split(".text")[0].split("\n")
        self.build_data(data_segment)
        print("memory")
        print(self.memory)
        print("labels")
        print(self.labels)



# to retrieve data:
# int(three + two + one + zero)
# if > 0x7FFFFFFF then -0x100000000