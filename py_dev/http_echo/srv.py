from http.server import BaseHTTPRequestHandler
from shutil import get_terminal_size


def _log_req(handler: BaseHTTPRequestHandler) -> None:
    cols, _ = get_terminal_size()
    print("*" * cols)

    method = handler.command
    path = handler.path
    headers = handler.headers.items()

    body_len = next(
        (int(val) for key, val in headers if key.lower() == "content-length"), 0
    )
    body = handler.rfile.read(body_len).decode()

    print(f"{method} {path}")
    print("::Headers::")
    for key, val in headers:
        print(f"{key}: {val}")
    if body:
        print("::Body::")
        print(body)


def _resp(handler: BaseHTTPRequestHandler) -> None:
    handler.send_response_only(200)
    handler.end_headers()
    handler.wfile.write(b"OK")


class EchoServer(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        _log_req(self)
        _resp(self)

    def do_POST(self) -> None:
        self.do_GET()

    def do_PUT(self) -> None:
        self.do_POST()
