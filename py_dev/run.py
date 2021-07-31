from asyncio import run
from sys import exit
from typing import Awaitable, NoReturn


def run_main(main: Awaitable[int]) -> NoReturn:
    try:
        code = run(main)
    except BrokenPipeError:
        exit(13)
    except KeyboardInterrupt:
        exit(130)
    else:
        exit(code)
