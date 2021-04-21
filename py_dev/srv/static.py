from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from locale import strxfrm
from mimetypes import guess_type
from pathlib import Path, PurePosixPath
from shutil import copyfileobj
from typing import Sequence, Tuple, Union
from urllib.parse import urlsplit

from std2.pathlib import is_relative_to


def _seek(
    handler: BaseHTTPRequestHandler, assets_dir: Path
) -> Union[Path, None, Sequence[Tuple[bool, Path]]]:
    uri = urlsplit(handler.path)
    path = PurePosixPath(uri.path)
    asset = (assets_dir / path).resolve()

    if not is_relative_to(asset, assets_dir) or not asset.exists():
        return None
    elif asset.is_dir():
        paths = sorted(
            ((path.is_dir(), path) for path in asset.iterdir()),
            key=lambda p: (p[0], strxfrm(str(p[1]))),
        )
        return paths
    else:
        return asset


def _send_headers(handler: BaseHTTPRequestHandler, asset: Path) -> None:
    stat = asset.stat()
    size = str(stat.st_size)
    last_mod = handler.date_time_string(int(stat.st_mtime))
    mime, encoding = guess_type(asset, strict=False)
    mt = mime or "application/octet-stream"

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", value=mt)
    if encoding:
        handler.send_header("Content-Encoding", encoding)
    handler.send_header("Content-Length", size)
    handler.send_header("Last-Modified", last_mod)
    handler.end_headers()


def head(handler: BaseHTTPRequestHandler, assets_dir: Path) -> None:
    asset = _seek(handler, assets_dir=assets_dir)
    if asset:
        _send_headers(handler, asset=asset)
    else:
        handler.send_error(HTTPStatus.NOT_FOUND)


def get(handler: BaseHTTPRequestHandler, assets_dir: Path) -> None:
    asset = _seek(handler, assets_dir=assets_dir)
    if asset:
        _send_headers(handler, asset=asset)
        with asset.open("rb") as fd:
            copyfileobj(fd, handler.wfile)
    else:
        handler.send_error(HTTPStatus.NOT_FOUND)
