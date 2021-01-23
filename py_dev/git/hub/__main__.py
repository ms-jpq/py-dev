from subprocess import check_output
from webbrowser import open as open_w

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


def main() -> None:
    upstream = check_output(
        ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"),
        text=True,
    )
    remote, _, branch = upstream.partition("/")
    uri = check_output(("git", "remote", "get-url", remote), text=True)

    clean_uri = _p_uri(uri, branch=branch)
    open_w(clean_uri)
    print(clean_uri)


run_main(main)
