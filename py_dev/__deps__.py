from os import environ
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, run
from sys import argv, path, stderr
from typing import Optional

_REQUIREMENTS = Path(__file__).parent / "requirements.txt"
_XDG_DATA_HOME = environ.get("XDG_DATA_HOME")
_RT_DIR = (
    (Path(_XDG_DATA_HOME) if _XDG_DATA_HOME else Path().home() / ".local" / "share")
    / "py_dev"
    / "runtime"
)
_DEPS_LOCK = _RT_DIR.parent / "deps.lock"
_RT_DIR.mkdir(parents=True, exist_ok=True)
path.append(str(_RT_DIR))


def _deps(err: Optional[Exception]) -> None:
    cmd = "pip3"
    if which(cmd):
        proc = run(
            (
                cmd,
                "install",
                "--upgrade",
                "--target",
                str(_RT_DIR),
                "--requirement",
                str(_REQUIREMENTS),
            ),
            cwd=_RT_DIR,
            stdin=DEVNULL,
            stdout=stderr,
        )
        if proc.returncode:
            exit(proc.returncode)
        else:
            _DEPS_LOCK.parent.mkdir(parents=True, exist_ok=True)
            _DEPS_LOCK.write_bytes(_REQUIREMENTS.read_bytes())
            proc = run(argv)
            exit(proc.returncode)
    else:
        if err:
            raise err


if (
    not _DEPS_LOCK.exists()
    or _DEPS_LOCK.read_text().strip() != _REQUIREMENTS.read_text().strip()
):
    _deps(None)
else:
    try:
        import markdown
        import pygments
        import std2
    except ImportError as e:
        _deps(e)
