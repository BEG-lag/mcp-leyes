"""Thin wrapper over the git command line: clone, fetch, log and blob reads.

The leyes-mx history is the database. A bare clone holds every version of every
law; ``git log`` lists the versions and ``git cat-file`` reads them. Nothing here
writes to the source repository.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

GIT_INSTALL_HELP = (
    "mcp-leyes necesita git instalado y en el PATH para leer el historial de las leyes. "
    "Instálalo desde https://git-scm.com/downloads (macOS: `xcode-select --install` o "
    "`brew install git`; Debian/Ubuntu: `apt install git`; Windows: `winget install Git.Git`) "
    "y reinicia el cliente MCP."
)

# Commit records: \x1e starts a commit, \x1f separates fields; --raw lines follow.
_LOG_FORMAT = "%x1e%H%x1f%aI%x1f%an%x1f%cI%x1f%B%x1f"


class GitError(RuntimeError):
    """A git command failed."""


class GitMissingError(GitError):
    """git is not installed or not on PATH."""

    def __init__(self) -> None:
        super().__init__(GIT_INSTALL_HELP)


def git_executable() -> str:
    exe = shutil.which("git")
    if not exe:
        raise GitMissingError()
    return exe


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",  # never block on a credential prompt
            "GIT_ASKPASS": "",
            "GCM_INTERACTIVE": "never",
            "LC_ALL": "C.UTF-8" if os.name != "nt" else env.get("LC_ALL", ""),
        }
    )
    return env


def run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    exe = git_executable()
    cmd = [exe, "-c", "core.quotepath=off", "-c", "i18n.logOutputEncoding=UTF-8", *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            env=_env(),
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git {' '.join(args[:2])} tardó más de {timeout:.0f} s") from exc
    except FileNotFoundError as exc:  # pragma: no cover - which() said it existed
        raise GitMissingError() from exc
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"
        raise GitError(f"git {' '.join(args[:2])} falló: {message}")
    return proc


@dataclass
class RawCommit:
    sha: str
    author_date: datetime
    author: str
    committer_date: datetime
    message: str
    files: dict[str, str] = field(default_factory=dict)  # path -> blob sha (after the commit)

    @property
    def dof_date(self) -> date:
        # leyes-mx sets GIT_AUTHOR_DATE to noon (Mexico City) of the DOF publication.
        return self.author_date.date()

    @property
    def subject(self) -> str:
        return self.message.split("\n", 1)[0].strip()


class BareRepo:
    """A bare clone of leyes-mx, read through git plumbing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._batch: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    # --------------------------------------------------------------- setup

    @staticmethod
    def clone(source: str, path: Path, *, timeout: float = 600) -> BareRepo:
        """Full bare clone into ``path`` (atomic: cloned next to it, then renamed)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        run_git(
            ["clone", "--bare", "--single-branch", "--quiet", source, str(tmp)],
            timeout=timeout,
        )
        try:
            tmp.rename(path)
        except OSError:
            # Another process finished first; keep its clone.
            shutil.rmtree(tmp, ignore_errors=True)
            if not (path / "HEAD").exists():
                raise
        return BareRepo(path)

    def exists(self) -> bool:
        return (self.path / "HEAD").exists() and (self.path / "objects").is_dir()

    def branch_ref(self) -> str:
        out = run_git(["symbolic-ref", "HEAD"], cwd=self.path).stdout.decode().strip()
        return out or "refs/heads/main"

    def fetch(self, *, timeout: float = 120) -> None:
        ref = self.branch_ref()
        run_git(
            ["fetch", "--quiet", "--prune", "origin", f"+{ref}:{ref}"],
            cwd=self.path,
            timeout=timeout,
        )

    def remote_url(self) -> str:
        proc = run_git(["config", "--get", "remote.origin.url"], cwd=self.path, check=False)
        return proc.stdout.decode().strip()

    def head(self) -> str:
        return run_git(["rev-parse", "HEAD"], cwd=self.path).stdout.decode().strip()

    # --------------------------------------------------------------- reads

    def log(self, paths: list[str], *, since_exclusive: str | None = None) -> list[RawCommit]:
        """Non-merge commits touching ``paths``, newest first, with the blob of each file."""
        args = [
            "log",
            "--no-merges",
            "--raw",
            "--no-abbrev",
            "--no-renames",
            "-z",
            f"--format={_LOG_FORMAT}",
        ]
        if since_exclusive:
            args.append(f"{since_exclusive}..HEAD")
        else:
            args.append("HEAD")
        args += ["--", *paths]
        out = run_git(args, cwd=self.path, timeout=300).stdout.decode("utf-8", "replace")
        commits: list[RawCommit] = []
        for record in out.split("\x1e"):
            if not record.strip("\x00\n"):
                continue
            fields = record.split("\x1f")
            if len(fields) < 6:
                continue
            sha, author_date, author, committer_date, message, raw = fields[:6]
            commit = RawCommit(
                sha=sha.strip(),
                author_date=datetime.fromisoformat(author_date.strip()),
                author=author.strip(),
                committer_date=datetime.fromisoformat(committer_date.strip()),
                message=message.strip(),
            )
            # With -z, raw entries are ":meta\0path\0" pairs.
            parts = list(raw.split("\x00"))
            i = 0
            while i < len(parts):
                meta = parts[i].strip("\n")
                if meta.startswith(":") and i + 1 < len(parts):
                    bits = meta[1:].split()
                    if len(bits) >= 5:
                        commit.files[parts[i + 1]] = bits[3]
                    i += 2
                else:
                    i += 1
            commits.append(commit)
        return commits

    def show(self, rev: str, path: str) -> str | None:
        """Contents of ``path`` at ``rev`` (None if it does not exist there)."""
        proc = run_git(["show", f"{rev}:{path}"], cwd=self.path, check=False)
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8", "replace")

    def blob(self, sha: str) -> str:
        """Read a blob through one long-lived ``git cat-file --batch`` process."""
        with self._lock:
            for attempt in (1, 2):
                proc = self._batch_process()
                try:
                    assert proc.stdin
                    assert proc.stdout
                    proc.stdin.write(sha.encode() + b"\n")
                    proc.stdin.flush()
                    header = proc.stdout.readline().decode().split()
                    if len(header) == 2 and header[1] == "missing":
                        raise GitError(f"objeto {sha} no encontrado en {self.path}")
                    if len(header) != 3:
                        raise GitError(f"respuesta inesperada de git cat-file: {header!r}")
                    size = int(header[2])
                    data = proc.stdout.read(size)
                    proc.stdout.read(1)  # trailing newline
                    return data.decode("utf-8", "replace")
                except (BrokenPipeError, OSError, ValueError):
                    self._close_batch()
                    if attempt == 2:
                        raise
        raise GitError("git cat-file no respondió")  # pragma: no cover

    def _batch_process(self) -> subprocess.Popen[bytes]:
        if self._batch is None or self._batch.poll() is not None:
            self._batch = subprocess.Popen(
                [git_executable(), "cat-file", "--batch"],
                cwd=self.path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=_env(),
            )
        return self._batch

    def _close_batch(self) -> None:
        if self._batch is not None:
            try:
                if self._batch.stdin:
                    self._batch.stdin.close()
                self._batch.terminate()
                self._batch.wait(timeout=5)
            except Exception:  # pragma: no cover - best effort
                pass
            self._batch = None

    def close(self) -> None:
        with self._lock:
            self._close_batch()

    def diff(self, old: str, new: str, path: str, *, word: bool = False) -> str:
        args = ["diff", "--no-color", "--unified=0"]
        if word:
            args.append("--word-diff=plain")
        args += [old, new, "--", path]
        return run_git(args, cwd=self.path).stdout.decode("utf-8", "replace")
