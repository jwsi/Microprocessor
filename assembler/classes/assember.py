import classes.errors as errors
from classes.instruction import Instruction
import re, pickle


class Assembler():
    """
    This class is the main assembler class defining all operations.
    """
    # Define input and output file
    assembly = None
    output_file = None

    # Define memory dictionary which will be dumped into machine code.
    next_address = 32 # Reserve first 64 for registers etc...
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
            print("memory:")
            for word in range(int(len(self.memory)/4)):
                if 32+4*word == self.main:
                    print("instructions:")
                print(str(32+4*word) + " "
                      + self.memory[32+4*word] + " "
                      + self.memory[32+4*word+1] + " "
                      + self.memory[32+4*word+2] + " "
                      + self.memory[32+4*word+3])
            print("main address: " + str(self.main))
        else:
            f = open(self.output_file, "wb")
            pickle.dump(self.memory, f)
            pickle.dump(self.main, f)
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
                binary_parameter = "{0:032b}".format(parameter)
                self.memory[self.next_address  ] = binary_parameter[0:8]
                self.memory[self.next_address+1] = binary_parameter[8:16]
                self.memory[self.next_address+2] = binary_parameter[16:24]
                self.memory[self.next_address+3] = binary_parameter[24:]
                self.next_address += 4


    def insert_instruction(self, address, instruction):
        """
        This inserts instructions into the memory dictionary.
        :param instruction: list containing parts of the instruction.
        """
        byte_instruction = Instruction(instruction).parse()
        self.memory[address] = byte_instruction[0]
        self.memory[address+1] = byte_instruction[1]
        self.memory[address+2] = byte_instruction[2]
        self.memory[address+3] = byte_instruction[3]


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
                address, instruction=self.next_address, [operation]
                for part in operand.split(","):
                    instruction.append(part.strip())
                self.instructions.append((address, instruction))
                self.next_address += 4


    def first_pass(self):
        """
        Allocates memory for data & instructions.
        Also identifies labels and associated addresses.
        """
        data_segment = self.assembly.split(".data")[1].split(".text")[0].split("\n")
        self.build_data(data_segment)
        instruction_segment = self.assembly.split(".text")[1].split("\n")
        self.build_instructions(instruction_segment)


    def second_pass(self):
        """
        Converts label names to addresses
        """
        raw_instructions = []
        for address, instruction in self.instructions:
            raw_instruction = [instruction[0]] + list(map(lambda x:
                                                          self.replace_parameter(x),
                                                          instruction[1:]))
            raw_instructions.append((address, raw_instruction))
        # Now we can remove all references to labels
        self.labels = None
        # Change the instructions to raw format
        self.instructions = raw_instructions
        for address, instruction in self.instructions:
            self.insert_instruction(address, instruction)


    def replace_parameter(self, parameter):
        """
        Replaces each instruction parameter with a decoded version and a memory offset.
        Otherwise return x.
        :param parameter: instruction parameter (potential label).
        :return: label address or original x.
        """
        parameter, offset = self.decode_parameter(parameter)
        try: # Register & immediate conversion
            return int(parameter), offset
        except ValueError:
            pass
        try: # Label conversion
            return self.labels[parameter], offset
        except KeyError:
            raise errors.InvalidLabel(parameter)


    def decode_parameter(self, parameter):
        """
        Decodes instruction parameters.
        :param parameter: instruction parameter.
        :return: parameter interpretation with associated memory offset.
        """
        result = re.search('([-0-9]*)\(*\$*([A-Za-z0-9_]*)\)*', parameter)
        offset = int(result.group(1) or 0)
        parameter = result.group(2)
        if not bool(parameter): # If parameter is not found then it's an immediate and offset should be used.
            return offset, 0
        if parameter in ["0", "zero"]: # Check for zero register
            return 0, offset
        elif parameter[0] == 't': # Check for temp register
            number = int(parameter[1])
            if number <= 7:
                return (number + 8), offset
            else:
                return (number + 16), offset
        elif parameter == "sp": # Check for stack pointer
            return 29, offset
        else: # Otherwise it's a label or immediate
            return parameter, offset





# to retrieve data:
# int(three + two + one + zero)
# if > 0x7FFFFFFF then -0x100000000