from argparse import ArgumentParser, Namespace
from collections.abc import AsyncIterator, Iterator
from re import RegexFlag, compile
from shlex import join
from typing import NoReturn, Pattern, Sequence

from std2.asyncio.subprocess import call

from ...log import log
from ...run import run_main


def _compile(pattern: str) -> Pattern:
    flags = RegexFlag.IGNORECASE if pattern.casefold() == pattern else RegexFlag.UNICODE
    return compile(pattern, flags=flags)


async def _git_branches(upstream: str) -> tuple[str, str]:
    await call("git", "fetch", "--all", capture_stderr=False)
    proc = await call("git", "branch", "--show-current", capture_stderr=False)
    working_branch = proc.stdout.rstrip().decode()
    cherry_branch = f"cherry/{working_branch}"
    await call(
        "git",
        "branch",
        "--no-track",
        "--",
        cherry_branch,
        upstream,
        capture_stderr=False,
    )
    return working_branch, cherry_branch


async def _git_commits(
    working_branch: str,
    cherry_branch: str,
    ignore: Sequence[Pattern],
    filter: Sequence[Pattern],
) -> AsyncIterator[str]:
    proc = await call(
        "git",
        "log",
        "--pretty=format:%H%x00%ae",
        f"${cherry_branch}..${working_branch}",
        capture_stderr=False,
    )

    for line in proc.stdout.decode().splitlines():
        sha, sep, email = line.partition("\0")
        assert sep

        if any(p.search(email) for p in ignore):
            pass
        elif not filter or any(p.search(email) for p in filter):
            yield sha


async def _git_stash() -> bool:
    async def stash() -> bytes:
        proc = await call("git", "stash", "list", capture_stderr=False)
        return proc.stdout

    pre = await stash()
    await call("git", "stash", "push", "--include-untracked", capture_stderr=False)
    post = await stash()
    return pre != post


async def _git_pick(
    working_branch: str, cherry_branch: str, commits: Sequence[str], dirty: bool
) -> None:
    await call("git", "switch", "--", cherry_branch, capture_stderr=False)
    await call(
        "git",
        "cherry-pick",
        "--keep-redundant-commits",
        "--allow-empty-message",
        "--",
        *reversed(commits),
        capture_stderr=False,
    )
    await call("git", "switch", "--", working_branch, capture_stderr=False)
    if dirty:
        await call("git", "stash", "pop", capture_stderr=False)


def _sh(cherry_branch: str, dirty: bool) -> None:
    def cont() -> Iterator[str]:
        if dirty:
            yield from ("git", "stash", "push", "--include-untracked")
            yield "&&"

        yield from ("git", "reset", "--hard", cherry_branch)

        if dirty:
            yield "&&"
            yield from ("git", "stash", "pop")

        yield "&&"
        yield from ("git", "branch", "--delete", "--", cherry_branch)

    log.info("%s", join(cont()))


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("upstream")
    parser.add_argument("-f", "--filter", type=_compile, nargs="*", default=())
    parser.add_argument("-i", "--ignore", type=_compile, nargs="*", default=())
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    upstream = args.upstream
    filter: Sequence[Pattern] = args.filter
    ignore: Sequence[Pattern] = args.ignore

    working_branch, cherry_branch = await _git_branches(upstream)
    commits = [
        c
        async for c in _git_commits(
            working_branch, cherry_branch=cherry_branch, ignore=ignore, filter=filter
        )
    ]

    if not commits:
        log.warn("%s", "No commits to cherry-pick")
        return 0
    else:
        dirty = await _git_stash()
        await _git_pick(
            working_branch, cherry_branch=cherry_branch, commits=commits, dirty=dirty
        )
        _sh(cherry_branch, dirty=dirty)

        return 0


def main() -> NoReturn:
    run_main(_main())
