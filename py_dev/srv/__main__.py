from argparse import ArgumentParser, Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import curdir
from os.path import normcase
from pathlib import Path, PurePath
from socket import getfqdn
from webbrowser import open as w_open

from std2.shutil import hr_print

from ..log import log
from ..run import run_main
from .static import build_j2, get, head


def _parse_args() -> Namespace:
    cwd = PurePath(normcase(curdir))
    parser = ArgumentParser()
    parser.add_argument("root", nargs="?", type=PurePath, default=cwd)
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    addr = "" if args.open else "localhost"
    bind = (addr, args.port)
    host = getfqdn() if args.open else "localhost"

    j2 = build_j2()
    try:
        root = Path(normcase(args.root)).resolve(strict=True)

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self) -> None:
                head(j2, handler=self, root=root)

            def do_GET(self) -> None:
                get(j2, handler=self, root=root)

        httpd = ThreadingHTTPServer(bind, Handler)
    except OSError as e:
        log.fatal("%s", hr_print(e))
        return 1
    else:
        encoded = host.encode("idna").decode()
        location = f"http://{encoded}:{args.port}"
        log.info("%s", hr_print(f"SERVING -- {location}"))
        w_open(location)
        httpd.serve_forever()
        return 0


run_main(main())
