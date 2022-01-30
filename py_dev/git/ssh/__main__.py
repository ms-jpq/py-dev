from argparse import ArgumentParser, Namespace
from os import environ, execle
from os.path import normcase
from pathlib import Path, PurePath
from shlex import join
from shutil import which
from typing import Sequence, Tuple


def _parse_args() -> Tuple[Namespace, Sequence[str]]:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("path", type=PurePath)
    return parser.parse_known_args()


def main() -> int:
    args, argv = _parse_args()
    path = PurePath(args.path)

    if path == PurePath("-"):
        addn = {}
    else:
        key_path = path if path.is_absolute() else Path.home() / ".ssh" / path
        ssh_cmd = join(("ssh", "-o", "IdentitiesOnly=yes", "-i", normcase(key_path)))
        addn = {"GIT_SSH_COMMAND": ssh_cmd}

    env = {**environ, **addn}

    if git := which("git"):
        execle(git, normcase(git), *argv, env)
    else:
        raise OSError(args.cmd)


main()
