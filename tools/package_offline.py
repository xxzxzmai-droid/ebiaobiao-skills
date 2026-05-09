#!/usr/bin/env python3
"""Build a clean offline installer archive for the e报表 skills."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "ebiaobiao-skills-offline"
INCLUDE = [
    ".gitignore",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "install.sh",
    "install.ps1",
    "skills",
    "tools/ebiao_quality_gate.py",
    "tools/package_offline.py",
]
EXCLUDED_DIRS = {".git", "node_modules", "dist", "__pycache__", "widgets", "docs"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name == "package-lock.json":
        return False
    return True


def iter_files() -> list[Path]:
    files: list[Path] = []
    for item in INCLUDE:
        path = ROOT / item
        if not path.exists():
            continue
        if path.is_file() and should_include(path):
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and should_include(child):
                    files.append(child)
    return sorted(files)


def add_zip(files: list[Path], output: Path, prefix: str) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            arcname = str(Path(prefix) / path.relative_to(ROOT))
            archive.write(path, arcname)


def add_tar(files: list[Path], output: Path, prefix: str) -> None:
    with tarfile.open(output, "w:gz") as archive:
        for path in files:
            arcname = str(Path(prefix) / path.relative_to(ROOT))
            archive.add(path, arcname=arcname)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build offline zip/tar.gz installers.")
    parser.add_argument("--out", default="dist", help="Output directory, default: dist")
    parser.add_argument("--name", default=DEFAULT_NAME, help=f"Archive base name, default: {DEFAULT_NAME}")
    args = parser.parse_args()

    out_dir = (ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    files = iter_files()
    if not files:
        raise SystemExit("no files to package")

    zip_path = out_dir / f"{args.name}.zip"
    tar_path = out_dir / f"{args.name}.tar.gz"
    add_zip(files, zip_path, args.name)
    add_tar(files, tar_path, args.name)

    print(f"files: {len(files)}")
    print(f"zip: {zip_path}")
    print(f"tar.gz: {tar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
