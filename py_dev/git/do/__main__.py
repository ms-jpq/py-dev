from subprocess import check_call
from sys import argv

from ...run import run_main


def main() -> None:
    check_call(("git", *argv))
    check_call(("git", "submodules", "foreach", "--recursive", *argv))


run_main(main)

