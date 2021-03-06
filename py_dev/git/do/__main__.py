from subprocess import check_call
from sys import argv

from ...run import run_main


def main() -> None:
    args = argv[1:]
    check_call(args)
    check_call(("git", "submodule", "foreach", "--recursive", *args))


run_main(main)

