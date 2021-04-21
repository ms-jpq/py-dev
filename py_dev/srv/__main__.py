from argparse import ArgumentParser, Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import getfqdn

from ..run import run_main
from .static import get, head


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("base", nargs="?", type=Path, default=Path("."))
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    addr = "" if args.open else "localhost"
    bind = (addr, args.port)

    host = getfqdn() if args.open else "localhost"
    print(f"SERVING -- http://{host}:{args.port}")

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self) -> None:
            head(self, assets_dir=args.base)

        def do_GET(self) -> None:
            get(self, assets_dir=args.base)

    httpd = ThreadingHTTPServer(bind, Handler)
    httpd.serve_forever()


run_main(main)
