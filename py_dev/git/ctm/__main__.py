from argparse import ArgumentParser, Namespace
from pathlib import Path
from subprocess import check_call, check_output

from ...run import run_main
from ..fzf import run_fzf
from ..ops import pretty_diff
from ..spec_parse import spec_parse


def _git_file_diff(sha1: str, sha2: str) -> bytes:
    return check_output(("git", "diff", "--name-only", "-z", sha1, sha2)).strip(b"\0")


def _git_diff_single(unified: int, sha1: str, sha2: str, path: str) -> bytes:
    return check_output(("git", "diff", f"--unified={unified}", sha1, sha2, "--", path))


def _fzf_lhs(unified: int, sha1: str, sha2: str, files: bytes) -> None:
    run_fzf(
        files,
        p_args=(sha1, sha2, f"--unified={unified}", "--preview={f1}"),
        e_args=(sha1, sha2, f"--unified={unified}", "--execute={f1}"),
    )


def _fzf_rhs(unified: int, sha1: str, sha2: str, path: str) -> None:
    diff = _git_diff_single(unified, sha1=sha1, sha2=sha2, path=path)
    pretty_diff(diff, path=path)


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("sha1")
    parser.add_argument("sha2")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview")
    group.add_argument("--execute")

    parser.add_argument("-u", "--unified", type=int, default=3)

    return spec_parse(parser)


def main() -> None:
    args = _parse_args()

    if args.preview:
        path = Path(args.preview).read_text().rstrip("\0")
        _fzf_rhs(args.unified, sha1=args.sha1, sha2=args.sha2, path=path)
    elif args.execute:
        path = Path(args.execute).read_text().rstrip("\0")
        _fzf_rhs(args.unified, sha1=args.sha1, sha2=args.sha2, path=path)
    else:
        commits = _git_file_diff(sha1=args.sha1, sha2=args.sha2)
        _fzf_lhs(args.unified, sha1=args.sha1, sha2=args.sha2, files=commits)


run_main(main)
