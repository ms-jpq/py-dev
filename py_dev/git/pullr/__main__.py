from argparse import ArgumentParser, Namespace
from subprocess import check_call

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("pr", type=int)
    parser.add_argument("-r", "--remote", default="origin")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    branch = f"pr-{args.pr}"
    check_call(("git", "fetch", "--", args.remote, f"pull/{args.pr}/head:{branch}"))
    check_call(("git", "switch", "--", branch))


run_main(main)
