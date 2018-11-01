import argparse
from classes.simulator import Simulator
from curses import wrapper


def main(stdscr, args):
    """
    Main function spawning the simulator.
    :param args: Arguments passed to simulator:
        source file name
    """
    simulator = Simulator(args.file, stdscr)
    simulator.simulate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JW MIPS Simulator")
    parser.add_argument('file', help="JW machine code file")
    args = parser.parse_args()
    wrapper(main, args)