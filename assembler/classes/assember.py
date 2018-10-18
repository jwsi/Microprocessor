import classes.errors as errors
from classes.instruction import Instruction


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
    instructions = []
    main = None


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
        """
        This inserts variables into the memory dictionary.
        :param label: variable name
        :param operand: operand for associated variable.
        """
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


    def insert_instruction(self, instruction):
        """
        This inserts instructions into the memory dictionary.
        :param instruction: list containing parts of the instruction.
        """
        instruction = Instruction(instruction)
        # parts = instruction.description()


    def build_data(self, data_segment):
        """
        This parses the data segment of the assembly code.
        :param data_segment: data section of assembly code.
        """
        for line in data_segment:
            if line.strip():
                if line.strip()[0] == "#":
                    # Ignore full line comments
                    continue
                label, operand = line.split(":")[0], line.split(":")[1].strip().split("#")[0]
                print(label + " " + operand)
                self.insert_data(label, operand)


    def build_instructions(self, instruction_segment):
        """
        This parses the instruction segment of the assembly code.
        :param instruction_segment: instruction segment of assembly code.
        """
        for line in instruction_segment:
            if len(line.split(":")) > 1:
                # Add label definition
                label = line.split(":")[0].strip()
                if label == 'main':
                    self.main = self.next_address
                self.labels[label] = self.next_address
            elif line.strip():
                if line.strip()[0] == "#":
                    # Ignore full line comments
                    continue
                operation, operand = line.strip().split(" ")[0], line.strip().split(" ", 1)[1].split("#")[0]
                instruction = [self.next_address]
                instruction.append(operation)
                for part in operand.split(","):
                    instruction.append(part.strip())
                self.instructions.append(instruction)
                self.next_address += 4
                print(instruction)


    def first_pass(self):
        """
        Allocates memory for data & instructions.
        Also identifies labels and associated addresses.
        """
        print("variables")
        data_segment = self.assembly.split(".data")[1].split(".text")[0].split("\n")
        self.build_data(data_segment)
        print()
        print("memory")
        print(self.memory)
        print()
        print("instructions")
        instruction_segment = self.assembly.split(".text")[1].split("\n")
        self.build_instructions(instruction_segment)
        print()
        print("labels")
        print(self.labels)


    def second_pass(self):
        """
        Converts label names to addresses
        """
        print()
        print("label converted instructions")
        raw_instructions = []
        for instruction in self.instructions:
            raw_instruction = instruction[0:2] + list(map(lambda x: self.replace_label(x), instruction[2:]))
            raw_instructions.append(raw_instruction)
            print(raw_instruction)
        # Now we can remove all references to labels
        self.labels = None
        # Change the instructions to raw format
        self.instructions = raw_instructions
        for instruction in self.instructions:
            self.insert_instruction(instruction)



    def replace_label(self, label):
        """
        Parses each instruction argument and returns the label address if found.
        Otherwise return x.
        :param label: instruction parameter (potential label).
        :return: label address or original x.
        """
        if "$" in label:
            return label
        try:
            return int(label)
        except ValueError:
            pass
        try:
            return self.labels[label]
        except KeyError:
            raise errors.InvalidLabel(label)




# to retrieve data:
# int(three + two + one + zero)
# if > 0x7FFFFFFF then -0x100000000