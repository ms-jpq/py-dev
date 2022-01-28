from asyncio import gather

from std2.asyncio.subprocess import call

from ...run import run_main


async def _switch(path: str) -> None:
    proc = await call(
        "git",
        "rev-parse",
        "--abbrev-ref",
        "origin/HEAD",
        cwd=path,
        capture_stderr=False,
    )

    origin_main = proc.out.decode().strip()
    _, _, main = origin_main.partition("/")
    await call(
        "git",
        "checkout",
        origin_main,
        cwd=path,
        capture_stdout=False,
        capture_stderr=False,
    )
    await call(
        "git",
        "switch",
        main,
        cwd=path,
        capture_stdout=False,
        capture_stderr=False,
    )


async def main() -> int:
    proc = await call(
        "git",
        "submodule",
        "foreach",
        "--recursive",
        "--quiet",
        "pwd",
        capture_stderr=False,
    )
    await gather(*map(_switch, proc.out.decode().splitlines()))
    return 0


run_main(main())
