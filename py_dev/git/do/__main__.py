from argparse import ArgumentParser, Namespace
from subprocess import check_call

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("args", nargs="+")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    a = args.args
    check_call(("git", *a))
    check_call(("git", "submodules", "foreach", "--recursive", *a))


run_main(main)

