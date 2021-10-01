from argparse import ArgumentParser, Namespace
from http.server import ThreadingHTTPServer
from socket import getfqdn

from std2.shutil import hr_print

from ..log import log
from ..run import run_main
from .srv import EchoServer


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    addr = "" if args.open else "localhost"
    bind = (addr, args.port)

    httpd = ThreadingHTTPServer(bind, EchoServer)
    host = getfqdn() if args.open else "localhost"
    log.info("%s", hr_print(f"SERVING -- http://{host}:{args.port}"))
    httpd.serve_forever()

    return 0


run_main(main())
