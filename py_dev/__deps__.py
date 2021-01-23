from os import environ
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, run
from sys import argv, path, stderr

_REQUIREMENTS = Path(__file__).parent / "requirements.txt"
_XDG_DATA_HOME = environ.get("XDG_DATA_HOME")
_RT_DIR = (
    (Path(_XDG_DATA_HOME) if _XDG_DATA_HOME else Path().home() / ".local" / "share")
    / "py_dev"
    / "runtime"
)
_RT_DIR.mkdir(parents=True, exist_ok=True)
path.append(str(_RT_DIR))


try:
    import pygments
    import std2
except ImportError:
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
            proc = run(argv)
            exit(proc.returncode)
    else:
        raise
