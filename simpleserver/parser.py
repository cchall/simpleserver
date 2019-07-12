import argparse
import sys


class ArgumentParserError(Exception):
    pass


class ArgumentParserWrapper(argparse.ArgumentParser):

    def error(self, message):
        self.print_usage(sys.stderr)
        raise ArgumentParserError(message)

    def print_help(self, file=None):
        # Prevent help from going to stderr. file parameter dummy retained for compatibility.
        print('new print statement')#, self.format_help())
        return 0


class ParserSetup:

    def __init__(self):
        parser = ArgumentParserWrapper(description='', add_help=False)
        parser.add_argument('mode', choices=('server', 'simulation', 'scan'))
        self.args = parser.parse_args(sys.argv[1:2])

    def __call__(self, *args, **kwargs):
        return getattr(self, self.args.mode)()

    def server(self):
        parser = ArgumentParserWrapper(description='Manage servers.', add_help=False)

        parser.add_argument('id', type=int)
        parser.add_argument('--clean', dest='remove_output', action='store_true')

        group1 = parser.add_mutually_exclusive_group()
        group1.add_argument('--add', dest='server_action', action='store_const', const='add_server')
        group1.add_argument('--remove', dest='server_action', action='store_const', const='remove_server')
        group1.add_argument('--stop', dest='server_action', action='store_const', const='stop_server')

        return parser.parse_args(sys.argv[2:])

    def simulation(self):
        parser = ArgumentParserWrapper(description='Start a single simulation.', add_help=False)
        parser.add_argument('--internal', dest='server_action', default='simulation')

        parser.add_argument('runfile', type=str)
        parser.add_argument('--name', type=str, required=True)
        parser.add_argument('--cores', type=int, required=True)
        parser.add_argument('--assignment', choices=['distributed, serial'], dest='mode', default='distributed')
        parser.add_argument('--priority', type=int, choices=[2, 1], default=2)
        parser.add_argument('--arguments', nargs='+', dest='args')

        return parser.parse_args(sys.argv[2:])


if __name__ == '__main__':
    my_parser = ParserSetup()
    print(my_parser().args)

