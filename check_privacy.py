"""Scan the repository for anything that could identify the author.

Run before every push. It looks for the things that actually leak in practice:
the local account name in a path, absolute home directories, and personal
identifiers accidentally committed in code, docs or workflow files.

    python check_privacy.py
    python check_privacy.py --add-name somepseudonym   # extra terms to allow-list
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Directories that never get committed, so leaks inside them do not matter.
SKIP_DIRS = {".git", "__pycache__", "site", "output", ".venv", "venv", "node_modules"}
SCAN_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".html", ".txt", ".json", ".cfg", ".toml"}

# Patterns that reveal a machine account or a real person.
PATTERNS = [
    ("absolute Windows home", re.compile(r"[A-Za-z]:\\+Users\\+[^\\\s\"']+", re.I)),
    ("git-bash Windows home", re.compile(r"/[a-z]/Users/[^/\s\"']+", re.I)),
    ("unix home directory", re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")),
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

# Addresses that are safe by design.
EMAIL_ALLOW = re.compile(r"@(users\.noreply\.github\.com|example\.com)$", re.I)


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in SCAN_SUFFIXES and p.name != Path(__file__).name:
                yield p


def scan(extra_terms: list[str]) -> list[str]:
    findings = []
    # The account this is running under is the single most likely leak.
    terms = {getpass.getuser().lower()} | {t.lower() for t in extra_terms if t}
    terms.discard("")

    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for term in terms:
                if term in low:
                    findings.append(f"{rel}:{lineno}: local account name '{term}' -> {line.strip()[:90]}")
            for label, rx in PATTERNS:
                for hit in rx.findall(line):
                    if label == "email address" and EMAIL_ALLOW.search(hit):
                        continue
                    findings.append(f"{rel}:{lineno}: {label} -> {hit[:90]}")
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the repo for identity leaks")
    ap.add_argument("--add-name", action="append", default=[],
                    help="extra term to flag (real name, old handle, ...)")
    args = ap.parse_args(argv)

    findings = sorted(set(scan(args.add_name)))
    if not findings:
        print("clean: no local paths, account names or personal addresses found")
        return 0
    print(f"{len(findings)} possible leak(s):\n")
    for f in findings:
        print("  " + f)
    print("\nReplace absolute paths with relative ones before committing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
