from argparse import ArgumentParser, Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from socket import getfqdn
from typing import Any

from std2.asyncio import go, run_in_executor

from ..log import log
from ..run import run_main
from .static import build_j2, get, head

_BASE = PurePosixPath("/")


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    addr = "" if args.open else "localhost"
    bind = (addr, args.port)
    root = Path(args.root).resolve()

    host = getfqdn() if args.open else "localhost"
    j2 = build_j2()

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self) -> None:
            head(j2, handler=self, base=_BASE, root=root)

        def do_GET(self) -> None:
            get(j2, handler=self, base=_BASE, root=root)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    httpd = ThreadingHTTPServer(bind, Handler)

    t = go(log, aw=run_in_executor(httpd.serve_forever))
    print(f"SERVING -- http://{host}:{args.port}", flush=True)
    try:
        await t
    except KeyboardInterrupt:
        await run_in_executor(httpd.shutdown)
        raise
    finally:
        await t

    return 0


run_main(main())
