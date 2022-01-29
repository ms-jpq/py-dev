from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address
from pathlib import Path, PurePath
from typing import Optional, Tuple

from std2.http.server import create_server
from std2.shutil import hr

from ..log import log
from .static import build_j2, get, head


def serve(
    root: PurePath, port: int, promiscuous: bool
) -> Optional[Tuple[HTTPServer, int]]:
    bind = ("" if promiscuous else ip_address("::1"), port)
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
        log.fatal("%s", hr(e))
        return None
    else:
        _, actual_port, *_ = httpd.socket.getsockname()
        return httpd, actual_port
