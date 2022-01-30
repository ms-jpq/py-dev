from http import HTTPStatus
from http.server import CGIHTTPRequestHandler, HTTPServer
from ipaddress import ip_address
from pathlib import PurePosixPath
from typing import Optional, Tuple
from urllib.parse import urlsplit

from std2.http.server import create_server
from std2.pathlib import POSIX_ROOT, is_relative_to
from std2.shutil import hr

from ...log import log

_CGI_BIN = POSIX_ROOT / "cgi-bin"
_CGI_SCRIPT = _CGI_BIN / "gitweb.cgi"


def _path(Handler: CGIHTTPRequestHandler) -> PurePosixPath:
    return PurePosixPath(urlsplit(Handler.path).path)


def _maybe_redirect(handler: CGIHTTPRequestHandler) -> None:
    # def redirect_path(self):
    #     if not self.path.startswith("/cgi-bin/gitweb.cgi"):
    #         self.path = self.path.replace("/cgi-bin/", "/")
    if _path(handler) == _CGI_BIN:
        handler.path = str(POSIX_ROOT)


def serve(port: int, promiscuous: bool) -> Optional[Tuple[HTTPServer, int]]:
    bind = ("" if promiscuous else ip_address("::1"), port)

    class Handler(CGIHTTPRequestHandler):
        def is_cgi(self) -> bool:
            if is_relative_to(_path(self), _CGI_SCRIPT):
                return super().is_cgi()
            else:
                return False

        def do_HEAD(self) -> None:
            _maybe_redirect(self)
            return super().do_HEAD()

        def do_GET(self) -> None:
            if _path(self) == POSIX_ROOT:
                self.send_response_only(HTTPStatus.SEE_OTHER)
                self.send_header("Location", str(_CGI_SCRIPT))
                self.end_headers()
            else:
                _maybe_redirect(self)
                super().do_GET()

        def do_POST(self) -> None:
            _maybe_redirect(self)
            super().do_POST()

    try:
        httpd = create_server(bind, Handler)
    except OSError as e:
        log.fatal("%s", hr(e))
        return None
    else:
        _, actual_port, *_ = httpd.socket.getsockname()
        return httpd, actual_port
