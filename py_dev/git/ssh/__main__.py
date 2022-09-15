from argparse import ArgumentParser, Namespace
from os import environ, execle
from os.path import normcase
from pathlib import Path, PurePath
from shlex import join
from shutil import which
from typing import NoReturn

from ...run import run_main


def _parse_args() -> Namespace:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("path", type=PurePath)
    parser.add_argument("argv", nargs="...")
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    path = PurePath(args.path)

    if path == PurePath("-"):
        addn = {}
    else:
        key_path = path if path.is_absolute() else Path.home() / ".ssh" / path
        ssh_cmd = join(("ssh", "-o", "IdentitiesOnly=yes", "-i", normcase(key_path)))
        addn = {"GIT_SSH_COMMAND": ssh_cmd}

    env = {**environ, **addn}

    cmd = "git"
    if git := which(cmd):
        execle(git, normcase(git), *args.argv, env)
    else:
        raise OSError(cmd)


def main() -> NoReturn:
    run_main(_main())
