from concurrent.futures import ThreadPoolExecutor
from subprocess import check_call, check_output

from ...run import run_main


def _switch(path: str) -> None:
    raw = check_output(
        (
            "git",
            "rev-parse",
            "--abbrev-ref",
            "origin/HEAD",
        ),
        text=True,
        cwd=path,
    )

    origin_main = raw.strip()
    _, _, main = origin_main.partition("/")
    check_call(("git", "checkout", origin_main), cwd=path)
    check_call(("git", "switch", main), cwd=path)


def main() -> None:
    with ThreadPoolExecutor() as pool:
        raw = check_output(
            ("git", "submodule", "foreach", "--recursive", "--quiet", "pwd"), text=True
        )
        tuple(pool.map(_switch, raw.splitlines()))


run_main(main)
