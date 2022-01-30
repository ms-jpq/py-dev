from argparse import ArgumentParser, Namespace
from webbrowser import open as w_open

from std2.shutil import hr

from ...log import log
from ...run import run_main
from .envsubst import envsubst
from .serve import serve


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=0)
    parser.add_argument("-o", "--open", action="store_true")
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    await envsubst()

    if httpd := serve(args.port, promiscuous=args.open):
        host = httpd.server_name if args.open else "localhost"
        location = f"http://{host}:{httpd.server_port}"
        w_open(location)

        log.info("%s", hr(f"GIT -- {location}"))
        httpd.serve_forever()
        return 0
    else:
        return 1


run_main(main())
