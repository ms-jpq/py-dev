from os import environ
from subprocess import run
from typing import Iterable

from .spec_parse import EOF, EXEC_SELF

_SHARED_OPTS = (
    "--read0",
    "--print0",
    "--ansi",
    "--preview-window=right:70%:wrap",
)


def run_fzf(stdin: bytes, p_args: Iterable[str], e_args: Iterable[str]) -> None:
    fin = f"--bind=return:abort+execute:{EOF.join(e_args)}"
    rhs = f"--preview={EOF.join(p_args)}"
    run(
        ("fzf", *_SHARED_OPTS, rhs, fin),
        env={**environ, "SHELL": EXEC_SELF},
        input=stdin,
    )
