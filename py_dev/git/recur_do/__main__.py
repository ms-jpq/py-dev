from argparse import ArgumentParser, Namespace
from pathlib import PurePath
from typing import Sequence, Tuple

from std2.asyncio.subprocess import call

from ...run import run_main


def _parse_args() -> Tuple[Namespace, Sequence[str]]:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("cmd", type=PurePath)
    return parser.parse_known_args()


async def main() -> int:
    args, argv = _parse_args()
    r_args = (args.cmd, *argv)

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


run_main(main())
