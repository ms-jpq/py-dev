from typing import Tuple
from urllib.parse import quote, urlsplit
from webbrowser import open as open_w

from std2.asyncio.subprocess import call
from std2.shutil import hr
from std2.string import removeprefix, removesuffix

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
    remote, _, branch = proc.stdout.decode().strip().partition("/")
    proc = await call(
        "git",
        "remote",
        "get-url",
        "--",
        remote,
        capture_stderr=False,
    )
    uri = proc.stdout.decode().strip()
    return branch, uri


def _p_uri(uri: str, branch: str) -> str:
    github_prefix = "git@github.com:"

    if urlsplit(uri).scheme in {"http", "https"}:
        return uri
    elif uri.startswith(github_prefix):
        location = removesuffix(removeprefix(uri, github_prefix), ".git")
        q_location, q_branch = quote(location), quote(branch)
        return f"https://github.com/{q_location}/tree/{q_branch}"
    else:
        raise ValueError(f"Cannot parse {uri} into https://...")


async def main() -> int:
    branch, uri = await _git_uri()
    clean_uri = _p_uri(uri, branch=branch)
    open_w(clean_uri)
    log.info("%s", hr(clean_uri))
    return 0


run_main(main())
