from http.server import BaseHTTPRequestHandler
from locale import strxfrm
from shutil import get_terminal_size
from typing import Mapping


def _log(method: str, path: str, headers: Mapping[str, str], content: bytes) -> None:
    cols, _ = get_terminal_size()
    print("*" * cols)
    print(f"{method.ljust(10)} {path}")
    print("::Headers::")
    for key, val in headers.items():
        print(f"{key}: {val}")
    body = content.decode(errors="replace")
    if body:
        print("::Body::")
        print(body)


def _echo_req(handler: BaseHTTPRequestHandler) -> None:
    headers = handler.headers.items()
    content_len = next(
        (int(val) for key, val in headers if key.lower() == "content-length"), 0
    )
    content = handler.rfile.read(content_len)

    handler.send_response_only(200)
    for key, val in handler.headers.items():
        handler.send_header(key, val)
    handler.end_headers()
    handler.wfile.write(content)

    _log(
        method=handler.command,
        path=handler.path,
        headers={k: v for k, v in sorted(headers, key=lambda t: strxfrm(t[0]))},
        content=content,
    )


class EchoServer(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        _echo_req(self)

    def do_POST(self) -> None:
        _echo_req(self)

    def do_PUT(self) -> None:
        _echo_req(self)
