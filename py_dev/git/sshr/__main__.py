from pathlib import PurePosixPath
from typing import Tuple
from urllib.parse import urlsplit

from std2.asyncio.subprocess import call
from std2.shutil import hr_print

from ...log import log
from ...run import run_main


async def _git_uri() -> Tuple[str, str]:
    proc = await call(
        "git",
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        capture_stderr=False,
    )
    remote, _, _ = proc.out.decode().strip().partition("/")
    proc = await call(
        "git",
        "remote",
        "get-url",
        remote,
        capture_stderr=False,
    )
    uri = proc.out.decode().strip()
    return remote, uri


async def _set_uri(remote: str, uri: str) -> None:
    await call(
        "git",
        "remote",
        "rm",
        remote,
        capture_stderr=False,
        capture_stdout=False,
    )
    await call(
        "git",
        "remote",
        "add",
        remote,
        uri,
        capture_stderr=False,
        capture_stdout=False,
    )


async def main() -> int:
    remote, uri = await _git_uri()
    parsed = urlsplit(uri)

    if parsed.scheme in {"http", "https"}:
        if parsed.netloc == "github.com":
            path = PurePosixPath(parsed.path).with_suffix("").relative_to("/")
            new_uri = f"git@{parsed.netloc}:{path}.git"
            await _set_uri(remote, uri=new_uri)
        else:
            raise ValueError(f"Cannot parse {uri}")
    else:
        new_uri = uri

    log.info("%s", hr_print(new_uri))
    return 0


run_main(main())
