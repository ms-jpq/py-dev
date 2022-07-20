from asyncio import run
from sys import exit
from typing import Any, Coroutine, NoReturn


def run_main(main: Coroutine[Any, Any, int]) -> NoReturn:
    try:
        code = run(main)
    except BrokenPipeError:
        exit(13)
    except KeyboardInterrupt:
        exit(130)
    else:
        exit(code)
