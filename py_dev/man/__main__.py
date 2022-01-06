from argparse import ArgumentParser, Namespace
from asyncio.tasks import gather
from os.path import normcase
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory
from typing import Optional
from urllib.parse import quote
from webbrowser import open as w_open

from std2.asyncio.subprocess import call
from std2.shutil import hr_print

from ..log import log
from ..run import run_main
from ..srv.serve import serve


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=0)
    parser.add_argument("-o", "--open", action="store_true")
    parser.add_argument("programs", nargs="+")
    return parser.parse_args()


async def _render(work_dir: Path, program: str) -> Optional[PurePath]:
    proc_1 = await call(
        "man",
        "-P",
        "tee",
        "--",
        program,
        capture_stdout=True,
        capture_stderr=False,
        check_returncode=set(),
    )

    if proc_1.code:
        return None
    else:
        title = f"[{program.upper()}]"
        proc_2 = await call(
            "man2html",
            "-compress",
            "-title",
            title,
            stdin=proc_1.out,
            capture_stdout=True,
            capture_stderr=False,
        )

        html = work_dir / f"{program}.html"
        html.write_bytes(proc_2.out)
        return html.relative_to(work_dir)


async def main() -> int:
    args = _parse_args()
    assert args.programs

    with TemporaryDirectory() as tmp:
        root = Path(tmp)

        maybe_htmls = await gather(
            *(_render(root, program=program) for program in {*args.programs})
        )

        if htmls := tuple(html for html in maybe_htmls if html):
            head, *rest = htmls
            web_path = "" if rest else quote(normcase(head))

            if srv := serve(root, port=args.port, promiscuous=args.open):
                httpd, port = srv
                host = httpd.server_name if args.open else "localhost"
                location = f"http://{host}:{port}/{web_path}"
                w_open(location)

                log.info("%s", hr_print(f"MAN -- {location}"))
                httpd.serve_forever()
                return 0
            else:
                return 1
        else:
            return 1


run_main(main())