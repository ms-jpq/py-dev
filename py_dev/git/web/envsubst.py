from asyncio.tasks import gather
from contextlib import suppress
from os import chdir, environ
from pathlib import Path, PurePath
from posixpath import normcase
from shutil import which
from string import ascii_letters

from std2.asyncio.subprocess import call

from ...j2 import build, render

_TEMPLATES = Path(__file__).resolve(strict=True).parent / "templates"


async def envsubst() -> None:
    ascii = {*ascii_letters, *{"_", "-"}}
    j2 = build(_TEMPLATES)

    if git := which("git"):
        p1, p2, p3, p4 = await gather(
            call(
                git,
                "--exec-path",
                capture_stderr=False,
            ),
            call(
                git,
                "--info-path",
                capture_stderr=False,
            ),
            call(
                git,
                "--no-optional-locks",
                "rev-parse",
                "--show-toplevel",
                capture_stderr=False,
            ),
            call(
                git,
                "--no-optional-locks",
                "rev-parse",
                "--git-common-dir",
                capture_stderr=False,
            ),
        )

        gitweb_src = Path(p2.stdout.decode()).parent / "gitweb"
        top_level = Path(p3.stdout.decode().rstrip())
        title = "".join(char if char in ascii else "-" for char in top_level.name)

        git_dir = top_level / p4.stdout.decode().rstrip()
        gitweb_dst = git_dir / "gitweb"

        cwd = gitweb_dst / "python"
        cgi_bin = cwd / "cgi-bin"
        cgi_bin.mkdir(parents=True, exist_ok=True)

        with suppress(FileExistsError):
            (cgi_bin / "gitweb.cgi").symlink_to(gitweb_src / "gitweb.cgi")
        with suppress(FileExistsError):
            (cgi_bin / "static").symlink_to(gitweb_src / "static")

        script = gitweb_dst / "gitweb_config.perl"
        script_env = {
            "TOP_LEVEL": top_level,
            "TMP": gitweb_dst / "tmp",
            "TITLE": title,
        }
        perl = render(j2, PurePath(script.name), env=script_env)
        script.write_text(perl)

        env = {
            "GIT_EXEC_PATH": normcase(p1.stdout.decode()),
            "GITWEB_CONFIG": normcase(script),
            "GIT_DIR": normcase(git_dir),
        }
        environ.update(env)
        chdir(cwd)
