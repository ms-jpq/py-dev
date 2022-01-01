from argparse import ArgumentParser, Namespace
from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address
from os import curdir
from os.path import normcase
from pathlib import Path, PurePath
from typing import Optional, Tuple
from webbrowser import open as w_open

from std2.http.server import create_server
from std2.shutil import hr_print

from ..log import log
from ..run import run_main
from .static import build_j2, get, head


def _parse_args() -> Namespace:
    cwd = PurePath(normcase(curdir))
    parser = ArgumentParser()
    parser.add_argument("root", nargs="?", type=PurePath, default=cwd)
    parser.add_argument("-o", "--open", type=int, default=0)
    return parser.parse_args()


def serve(root: PurePath, port: int) -> Optional[Tuple[HTTPServer, int]]:
    bind = ("" if port else ip_address("::1"), port)
    j2 = build_j2()

    try:
        resolved = Path(root).resolve(strict=True)

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self) -> None:
                head(j2, handler=self, root=resolved)

            def do_GET(self) -> None:
                get(j2, handler=self, root=resolved)

        httpd = create_server(bind, Handler)
    except OSError as e:
        log.fatal("%s", hr_print(e))
        return None
    else:
        _, actual_port, *_ = httpd.socket.getsockname()
        return httpd, actual_port


async def main() -> int:
    args = _parse_args()

    if srv := serve(args.root, port=args.open):
        httpd, port = srv
        host = httpd.server_name if args.open else "localhost"
        location = f"http://{host}:{port}"
        w_open(location)

        log.info("%s", hr_print(f"SERVING -- {location}"))
        httpd.serve_forever()
        return 0
    else:
        return 1


run_main(main())
