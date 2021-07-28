from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from locale import strxfrm
from mimetypes import guess_type
from os import sep
from pathlib import Path, PurePath, PurePosixPath
from shutil import copyfileobj
from stat import S_ISDIR
from typing import Optional, Sequence, Tuple, Union
from urllib.parse import unquote, urlsplit

from jinja2 import Environment
from std2.datetime import utc_to_local
from std2.locale import si_prefixed
from std2.pathlib import is_relative_to

from ..j2 import build, render

_TEMPLATES = Path(__file__).resolve().parent / "templates"
_INDEX = PurePath("index.html")


@dataclass(frozen=True)
class _Fd:
    path: Path
    sortby: Tuple[bool, str, str]
    rel_path: PurePath
    name: str
    mime: Optional[str]
    size: int
    mtime: datetime


def _fd(root: Path, path: Path) -> Optional[_Fd]:
    try:
        stat = path.stat()
    except PermissionError:
        return None
    else:
        is_dir = S_ISDIR(stat.st_mode)
        sortby = (not is_dir, strxfrm(path.suffix), strxfrm(path.stem))
        rel_path = path.relative_to(root)
        name = path.name + sep if is_dir else path.name

        if is_dir:
            mime = None
        else:
            mime, _ = guess_type(path, strict=False)

        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        fd = _Fd(
            path=path,
            sortby=sortby,
            rel_path=rel_path,
            name=name,
            mime=mime,
            size=stat.st_size,
            mtime=mtime,
        )
        return fd


def _seek(
    handler: BaseHTTPRequestHandler, base: PurePosixPath, root: Path
) -> Union[_Fd, Sequence[_Fd], None]:
    uri = urlsplit(handler.path)
    raw = unquote(uri.path)
    path = PurePosixPath(raw).relative_to(base)
    asset = (root / path).resolve()

    if not is_relative_to(asset, root) or not asset.exists():
        return None
    elif asset.is_dir():
        try:
            return sorted(
                (
                    fd
                    for fd in (_fd(root, path=child) for child in asset.iterdir())
                    if fd
                ),
                key=lambda fd: fd.sortby,
            )
        except PermissionError:
            return None
    else:
        return _fd(root, path=asset)


def _send_headers(handler: BaseHTTPRequestHandler, fd: _Fd) -> None:
    mimetype = fd.mime or "application/octet-stream"
    last_mod = format_datetime(fd.mtime, usegmt=True)

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", value=mimetype)
    handler.send_header("Content-Length", str(fd.size))
    handler.send_header("Last-Modified", last_mod)
    handler.end_headers()


def _index(j2: Environment, fd: Sequence[_Fd]) -> bytes:
    env = {
        "PATHS": (
            (
                f.name,
                f.mime,
                si_prefixed(f.size, precision=2),
                utc_to_local(f.mtime).replace(microsecond=0).strftime("%x %X %Z"),
            )
            for f in fd
        )
    }
    index = render(j2, path=_INDEX, env=env)
    return index.encode()


def _send_index_headers(handler: BaseHTTPRequestHandler, index: bytes) -> None:
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", value="text/html")
    handler.send_header("Content-Length", str(len(index)))
    handler.end_headers()


def build_j2() -> Environment:
    j2 = build(_TEMPLATES)
    return j2


def head(
    j2: Environment, handler: BaseHTTPRequestHandler, base: PurePosixPath, root: Path
) -> None:
    fd = _seek(handler, base=base, root=root)
    if fd is None:
        handler.send_error(HTTPStatus.NOT_FOUND)
    elif isinstance(fd, Sequence):
        index = _index(j2, fd=fd)
        _send_index_headers(handler, index=index)
    else:
        _send_headers(handler, fd=fd)


def get(
    j2: Environment, handler: BaseHTTPRequestHandler, base: PurePosixPath, root: Path
) -> None:
    fd = _seek(handler, base=base, root=root)

    if fd is None:
        handler.send_error(HTTPStatus.NOT_FOUND)
    elif isinstance(fd, Sequence):
        index = _index(j2, fd=fd)
        _send_index_headers(handler, index=index)
        handler.wfile.write(index)
    else:
        _send_headers(handler, fd=fd)
        with fd.path.open("rb") as pp:
            copyfileobj(pp, handler.wfile)

