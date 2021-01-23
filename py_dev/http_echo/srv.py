from http.server import BaseHTTPRequestHandler
from shutil import get_terminal_size


def _echo_req(handler: BaseHTTPRequestHandler) -> None:
    """
    Parse
    """

    method = handler.command
    path = handler.path
    headers = handler.headers.items()
    content_len = next(
        (int(val) for key, val in headers if key.lower() == "content-length"), 0
    )
    raw = handler.rfile.read(content_len)

    """
    Reply
    """

    handler.send_response_only(200)
    for key, val in handler.headers.items():
        handler.send_header(key, val)
    handler.end_headers()
    handler.wfile.write(raw)

    """
    Log
    """

    cols, _ = get_terminal_size()
    print("*" * cols)
    print(f"{method.ljust(10)} {path}")
    print("::Headers::")
    for key, val in headers:
        print(f"{key}: {val}")
    body = raw.decode(errors="replace")
    if body:
        print("::Body::")
        print(body)


class EchoServer(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        _echo_req(self)

    def do_POST(self) -> None:
        _echo_req(self)

    def do_PUT(self) -> None:
        _echo_req(self)
