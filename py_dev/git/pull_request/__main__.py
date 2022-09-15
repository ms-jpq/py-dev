from argparse import ArgumentParser, Namespace
from pathlib import PurePosixPath
from typing import NoReturn
from urllib.parse import unquote, urlsplit

from std2.asyncio.subprocess import call

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("uri")
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    path = PurePosixPath(unquote(urlsplit(args.uri).path))

    pr_id = int(path.name)
    br_name = f"pr-{pr_id}"

    await call(
        "git",
        "fetch",
        "origin",
        f"pull/{pr_id}/head:{br_name}",
        capture_stdout=False,
        capture_stderr=False,
    )
    await call(
        "git",
        "switch",
        br_name,
        capture_stdout=False,
        capture_stderr=False,
    )
    return 0


def main() -> NoReturn:
    run_main(_main())

