from argparse import ArgumentParser, Namespace
from asyncio import gather
from pathlib import PurePath
from typing import Sequence, Tuple

from std2.asyncio.subprocess import call

from ...run import run_main


def _parse_args() -> Tuple[Namespace, Sequence[str]]:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("cmd", type=PurePath)
    return parser.parse_known_args()


async def _switch(path: str) -> None:
    pass


async def main() -> int:
    proc = await call(
        "git",
        "submodule",
        "foreach",
        "--recursive",
        "--quiet",
        "pwd",
        capture_stderr=False,
    )
    await gather(*map(_switch, proc.out.decode().splitlines()))
    return 0


run_main(main())
