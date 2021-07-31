from webbrowser import open as open_w

from std2.asyncio.subprocess import call
from std2.string import removeprefix, removesuffix

from ...run import run_main


def _p_uri(uri: str, branch: str) -> str:
    if uri.startswith("http"):
        return uri
    elif uri.startswith("git@github.com:"):
        location = removesuffix(removeprefix(uri, "git@github.com:"), ".git")
        return f"https://github.com/{location}/tree/{branch}"
    else:
        raise ValueError(f"Cannot parse {uri} into https://...")


async def main() -> int:
    proc = await call(
        "git",
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        capture_stderr=False,
    )
    remote, _, branch = proc.out.decode().strip().partition("/")
    proc = await call(
        "git",
        "remote",
        "get-url",
        remote,
        capture_stderr=False,
    )

    clean_uri = _p_uri(proc.out.decode().strip(), branch=branch)
    open_w(clean_uri)
    print(clean_uri)
    return 0


run_main(main())
