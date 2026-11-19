#!/usr/bin/env python3
"""Register or remove an optional Codex SEO checkout skill."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]


def _extension_guide(root: Path, extension: str) -> Path:
    extensions = root / "extensions"
    matches = list((extensions / extension / "skills").glob("seo-*/SKILL.md"))
    if len(matches) != 1 or not matches[0].resolve().is_relative_to(extensions):
        raise ValueError(f"No unique checkout skill for {extension!r}.")
    return matches[0]


def _entry(root: Path, guide: Path, *, legacy_root: str | None = None) -> bytes:
    name = guide.parent.name
    relative_guide = guide.relative_to(root).as_posix()
    if legacy_root is None:
        guide_location = (
            f"Read the [extension guide](../../../{relative_guide}) and its linked references.\n"
            "Resolve the link from this SKILL.md. Its checkout root is three directories above\n"
            "this file's directory. When auditing another project, keep that\n"
        )
    else:
        guide_location = (
            "Read the Codex SEO checkout guide and its linked references before using this integration.\n"
            f"The guide is `{relative_guide}` relative to the checkout root.\n"
            f"The checkout root is `{legacy_root}`. When auditing another project, keep that\n"
        )
    return (
        f"---\nname: {name}\n"
        f"description: Use the optional {name.removeprefix('seo-')} integration for Codex SEO.\n"
        "---\n\n"
        f"{guide_location}"
        "project as the working directory and use the quoted absolute path to the checkout's\n"
        "`scripts/codex-seo` launcher. Ask before any paid or write operation.\n"
    ).encode()


def _is_legacy_entry(content: bytes, root: Path, guide: Path) -> bool:
    try:
        _, _, path_line = content.decode().partition("\nThe checkout root is `")
    except UnicodeDecodeError:
        return False
    old_root, _, _ = path_line.partition("`. When auditing another project, keep that\n")
    if not (PurePosixPath(old_root).is_absolute() or PureWindowsPath(old_root).is_absolute()):
        return False
    return content == _entry(root, guide, legacy_root=old_root)


def _create_exclusive(path: Path, content: bytes, mode: int = 0o600) -> bool:
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
    except OSError:
        path.unlink(missing_ok=True)
        raise
    return True


def _refresh_entry(path: Path, previous: bytes, content: bytes) -> None:
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".skill-")
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        if path.is_symlink() or path.read_bytes() != previous:
            raise ValueError(f"Existing skill changed and was left in place: {path}.")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def manage_skill(root: Path, extension: str, action: str) -> None:
    guide = _extension_guide(root, extension)
    target = root / ".agents" / "skills" / guide.parent.name / "SKILL.md"
    if any(parent.is_symlink() for parent in (target, *target.parents) if parent.is_relative_to(root)):
        raise ValueError(f"Refusing to change a symlink at or above {target}.")
    content = _entry(root, guide)
    if action == "install":
        target.parent.mkdir(parents=True, exist_ok=True)
        if _create_exclusive(target, content):
            print(f"Installed {target}.")
            return
    elif not target.exists():
        print(f"No checkout skill to remove: {target}.")
        return

    previous = target.read_bytes()
    legacy = previous != content and _is_legacy_entry(previous, root, guide)
    if previous != content and not legacy:
        raise ValueError(f"Existing skill differs and was left in place: {target}.")
    if action == "uninstall":
        target.unlink()
        if not any(target.parent.iterdir()):
            target.parent.rmdir()
        print(f"Removed {target}.")
    elif legacy:
        _refresh_entry(target, previous, content)
        print(f"Updated checkout skill: {target}.")
    else:
        print(f"Already installed: {target}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    extensions = sorted(installer.parent.name for installer in (ROOT / "extensions").glob("*/install.sh"))
    parser.add_argument("extension", choices=extensions)
    parser.add_argument("--create-shopify-env", action="store_true", help="Create a placeholders-only .shopify-env in the current audit folder.")
    args = parser.parse_args()
    if args.create_shopify_env and (args.extension, args.action) != ("shopify", "install"):
        parser.error("--create-shopify-env applies to Shopify installation only")
    try:
        manage_skill(ROOT, args.extension, args.action)
        if args.create_shopify_env:
            target = Path.cwd() / ".shopify-env"
            template = ROOT / "extensions/shopify/.shopify-env.example"
            if _create_exclusive(target, template.read_bytes()):
                print(f"Created {target} with placeholders. Restrict access before adding a signature.")
            else:
                print(f"Already exists: {target}. Left in place.")
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    if args.action == "install":
        print(f"See {ROOT / 'extensions' / args.extension / 'docs'} for prerequisites and setup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
