from os import environ
from sys import argv

from std2.asyncio.subprocess import call

from .spec_parse import ARGV_ENV, EOF, EXECUTE_HEAD, PREVIEW_HEAD

_SHARED_OPTS = (
    "--read0",
    "--print0",
    "--multi",
    "--ansi",
    "--preview-window=right:70%:wrap",
)


async def run_fzf(stdin: bytes) -> None:
    sh, *args = argv
    fin = f"--bind=return:abort+execute:{EXECUTE_HEAD}{{+f}}"
    rhs = f"--preview={PREVIEW_HEAD}{{+f}}"
    await call(
        "fzf",
        *_SHARED_OPTS,
        rhs,
        fin,
        env={**environ, ARGV_ENV: EOF.join(args), "LC_ALL": "C", "SHELL": sh},
        stdin=stdin,
        capture_stdout=False,
        capture_stderr=False,
        check_returncode={0, 130},
    )
