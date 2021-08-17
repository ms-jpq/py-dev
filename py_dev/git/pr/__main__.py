from argparse import ArgumentParser, Namespace
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from std2.asyncio.subprocess import call

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("uri")

    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    uri = urlsplit(args.uri)
    path = PurePosixPath(uri.path)
    pr_id = int(path.name)
    br_name = f"pr-{pr_id}"

    await call(
        "git",
        "fetch",
        "origin",
        f"pull/{pr_id}/HEAD:{br_name}",
        capture_stdout=False,
        capture_stderr=False,
    )

    await call(
        "git",
        "checkout",
        "--",
        br_name,
        capture_stdout=False,
        capture_stderr=False,
    )
    return 0


run_main(main())