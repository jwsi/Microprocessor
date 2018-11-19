import argparse
from classes.simulator import Simulator
from curses import wrapper
from classes.constants import debug
from classes.errors import Interrupt


def main(stdscr, args):
    """
    Main function spawning the simulator.
    :param args: Arguments passed to simulator:
        source file name
    """
    simulator = Simulator(args.file, stdscr)
    try:
        simulator.simulate()
    except Interrupt:
        if debug:
            exit(0)
        simulator.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JW MIPS Simulator")
    parser.add_argument('file', help="JW machine code file")
    args = parser.parse_args()
    if debug:
        main(None, args)
    wrapper(main, args)