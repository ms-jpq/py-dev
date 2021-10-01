from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from locale import strxfrm
from os import linesep
from typing import Any, Iterator, Mapping

from std2.shutil import hr_print

from ..log import log


def _log(method: str, path: str, headers: Mapping[str, Any], content: bytes) -> None:
    def cont() -> Iterator[str]:
        yield f"{method.ljust(10)} {path}"
        for key, val in headers.items():
            yield "::Headers::"
            yield f"{key}: {val}"
        if body := content.decode("UTF-8", errors="replace"):
            yield "::Body::"
            yield body

    lines = linesep.join(cont())
    log.info("%s", hr_print(lines))


def _echo_req(handler: BaseHTTPRequestHandler) -> None:
    headers = {
        k: v
        for k, v in sorted(
            handler.headers.items(), key=lambda t: strxfrm(next(iter(t)))
        )
    }
    content_len = next(
        (int(val) for key, val in headers.items() if key.lower() == "content-length"), 0
    )
    content = handler.rfile.read(content_len)

    handler.send_response(HTTPStatus.OK)
    for key, val in headers.items():
        handler.send_header(key, val)
    handler.end_headers()
    handler.wfile.write(content)

    _log(
        method=handler.command,
        path=handler.path,
        headers=headers,
        content=content,
    )


class EchoServer(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        _echo_req(self)

    def do_GET(self) -> None:
        _echo_req(self)

    def do_POST(self) -> None:
        _echo_req(self)

    def do_PUT(self) -> None:
        _echo_req(self)
