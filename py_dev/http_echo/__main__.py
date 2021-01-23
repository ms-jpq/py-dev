#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from http.server import ThreadingHTTPServer
from socket import getfqdn

from .srv import EchoServer


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    addr = "" if args.open else "localhost"
    bind = (addr, args.port)

    host = getfqdn() if args.open else "localhost"
    print(f"SERVING -- http://{host}:{args.port}")

    httpd = ThreadingHTTPServer(bind, EchoServer)
    httpd.serve_forever()
