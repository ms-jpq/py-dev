from sys import argv

from std2.asyncio.subprocess import call

from ...run import run_main


async def main() -> int:
    args = argv[1:]
    await call(
        *args,
        capture_stdout=False,
        capture_stderr=False,
    )
    await call(
        "git",
        "submodule",
        "foreach",
        "--recursive",
        *args,
        capture_stdout=False,
        capture_stderr=False,
    )
    return 0


run_main(main())
