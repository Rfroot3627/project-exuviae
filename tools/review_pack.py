#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> str:
    """Run command and return stdout+stderr (utf-8). Raises on non-zero."""
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return p.stdout


def try_run(cmd: list[str], cwd: Path) -> str:
    """Run command and return output; never raises."""
    try:
        return run(cmd, cwd)
    except Exception as e:
        return f"[ERROR] {cmd}\n{e}\n"


def ensure_git_repo(repo: Path) -> None:
    out = try_run(["git", "rev-parse", "--is-inside-work-tree"], repo).strip()
    if out != "true":
        print("這個路徑看起來不是 git repo：", repo)
        sys.exit(2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(
        description="Generate a lightweight review bundle for code supervision (git-based)."
    )
    ap.add_argument("--repo", default=".", help="repo root path (default: .)")
    ap.add_argument(
        "--base",
        default=None,
        help="base ref for diff (e.g. main, origin/main, <commit>). If omitted, use working tree diff.",
    )
    ap.add_argument(
        "--out",
        default="review_bundles",
        help="output directory (default: review_bundles)",
    )
    ap.add_argument(
        "--zip",
        action="store_true",
        help="also create a .zip archive (Windows-friendly)",
    )
    ap.add_argument(
        "--max-file-bytes",
        type=int,
        default=600_000,
        help="max bytes per file when dumping added files (default: 600k)",
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    ensure_git_repo(repo)

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_dir = Path(args.out).resolve() / f"hub_review_{ts}"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # 0) Head / branch / remotes
    write_text(bundle_dir / "00_head.txt", try_run(["git", "rev-parse", "HEAD"], repo))
    write_text(bundle_dir / "00_branch.txt", try_run(["git", "branch", "--show-current"], repo))
    write_text(bundle_dir / "00_remotes.txt", try_run(["git", "remote", "-v"], repo))

    # 1) status
    write_text(bundle_dir / "01_status_porcelain.txt", try_run(["git", "status", "--porcelain"], repo))
    write_text(bundle_dir / "01_status_full.txt", try_run(["git", "status"], repo))

    # Diff target:
    # - If base is provided: diff base...HEAD (or base..HEAD) + name-status
    # - Else: diff working tree (unstaged+staged), and also staged separately
    base = args.base

    if base:
        # name-status
        write_text(
            bundle_dir / "02_changed_files_name_status.txt",
            try_run(["git", "diff", "--name-status", f"{base}...HEAD"], repo),
        )
        # stat
        write_text(
            bundle_dir / "03_diff_stat.txt",
            try_run(["git", "diff", "--stat", f"{base}...HEAD"], repo),
        )
        # full diff
        write_text(
            bundle_dir / "04_diff.patch",
            try_run(["git", "diff", f"{base}...HEAD"], repo),
        )
        # added files list (relative paths)
        added = try_run(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"], repo).splitlines()
    else:
        # working tree name-status (includes staged+unstaged)
        write_text(
            bundle_dir / "02_changed_files_name_status.txt",
            try_run(["git", "diff", "--name-status"], repo),
        )
        write_text(
            bundle_dir / "02_changed_files_name_status_staged.txt",
            try_run(["git", "diff", "--cached", "--name-status"], repo),
        )
        write_text(
            bundle_dir / "03_diff_stat.txt",
            try_run(["git", "diff", "--stat"], repo),
        )
        write_text(
            bundle_dir / "03_diff_stat_staged.txt",
            try_run(["git", "diff", "--cached", "--stat"], repo),
        )
        write_text(
            bundle_dir / "04_diff.patch",
            try_run(["git", "diff"], repo),
        )
        write_text(
            bundle_dir / "04_diff_staged.patch",
            try_run(["git", "diff", "--cached"], repo),
        )
        # added files from working tree diff is ambiguous; we can approximate via staged diff if staged exists,
        # otherwise fallback to git status porcelain parsing.
        added = []
        staged_added = try_run(["git", "diff", "--cached", "--name-only", "--diff-filter=A"], repo).splitlines()
        if staged_added and any(x.strip() for x in staged_added):
            added = [x for x in staged_added if x.strip()]
        else:
            # parse status porcelain for ?? and A
            st = try_run(["git", "status", "--porcelain"], repo).splitlines()
            for line in st:
                if line.startswith("?? "):
                    added.append(line[3:].strip())

    # 5) Dump added file contents (full or truncated)
    dump_dir = bundle_dir / "05_added_files"
    dump_dir.mkdir(parents=True, exist_ok=True)

    preview_lines = []
    max_bytes = args.max_file_bytes

    for rel in added:
        rel = rel.strip()
        if not rel:
            continue
        p = repo / rel
        if not p.exists() or p.is_dir():
            continue

        # Limit very large files
        try:
            size = p.stat().st_size
        except Exception:
            size = -1

        safe_name = rel.replace("/", "__").replace("\\", "__")
        out_path = dump_dir / f"{safe_name}.txt"

        try:
            data = p.read_bytes()
            if size > max_bytes:
                data = data[:max_bytes] + b"\n\n[TRUNCATED]\n"
            out_path.write_bytes(data)
            preview_lines.append(f"{rel}  ({size} bytes)")
        except Exception as e:
            write_text(out_path, f"[ERROR reading {rel}] {e}\n")

    write_text(bundle_dir / "05_added_files_index.txt", "\n".join(preview_lines) + ("\n" if preview_lines else ""))

    # 6) Helpful command hints (fill in by hand)
    hints = """# 你可以把下面填好，一起貼給審查者
# 啟動指令：
#   python -m ...
# 或
#   uvicorn ...

# 驗證指令（例）：
#   curl -i http://127.0.0.1:8000/healthz
"""
    write_text(bundle_dir / "06_run_notes.txt", hints)

    # Zip (optional)
    if args.zip:
        zip_path = shutil.make_archive(str(bundle_dir), "zip", root_dir=str(bundle_dir))
        print("OK 產出審查包資料夾：", bundle_dir)
        print("OK 產出 zip：", zip_path)
    else:
        print("OK 產出審查包資料夾：", bundle_dir)


if __name__ == "__main__":
    main()
