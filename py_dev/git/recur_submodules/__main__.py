from argparse import ArgumentParser, Namespace
from pathlib import PurePath
from typing import NoReturn

from std2.asyncio.subprocess import call

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("cmd", type=PurePath)
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    r_args = (args.cmd, *args.argv)

    await call(
        *r_args,
        capture_stdout=False,
        capture_stderr=False,
    )
    await call(
        "git",
        "submodule",
        "foreach",
        "--recursive",
        *r_args,
        capture_stdout=False,
        capture_stderr=False,
    )
    return 0


def main() -> NoReturn:
    run_main(_main())
