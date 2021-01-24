from os import linesep
from shlex import join
from sys import stdout


def print_git_show(sha: str, path: str) -> None:
    end = linesep if stdout.isatty() else ""
    cmd = join(("git", "show", f"{sha}~:{path}"))
    print(cmd, end=end)
