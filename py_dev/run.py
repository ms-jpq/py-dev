from sys import exit
from typing import Callable


def run_main(main: Callable[[], None]) -> None:
    try:
        main()
    except BrokenPipeError:
        exit(13)
    except KeyboardInterrupt:
        exit(130)
