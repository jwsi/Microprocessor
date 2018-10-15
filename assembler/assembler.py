import argparse
from classes.assember import Assembler


def main(args):
    """
    Main function spawning the assembler.
    :param args: Arguments passed to assembler:
        source file name
        output file name
    :return: Machine code written to output or stdout if None specified.
    """
    assembler = Assembler(args.file, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JW MIPS Assember")
    parser.add_argument('-o', '--output', metavar='file', help="Destination for binary file")
    parser.add_argument('file', help="MIPS assembly source file")
    args = parser.parse_args()
    main(args)