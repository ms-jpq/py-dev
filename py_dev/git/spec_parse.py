from argparse import ArgumentParser, Namespace
from sys import argv

EOF = "\04"


def spec_parse(parser: ArgumentParser) -> Namespace:
    try:
        _, a1, a2 = argv
        if a1 == "-c":
            return parser.parse_args(a2.split(EOF))
        else:
            return parser.parse_args()
    except ValueError:
        return parser.parse_args()
