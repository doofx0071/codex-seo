#!/usr/bin/env python3
"""Synchronize the repo-local SEO skill from the portable plugin."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile

from build_plugin import PACKAGE, ROOT, SKILL_PATH, package_files, read_package, skill_file_allowed

MIRROR = ROOT / ".agents" / SKILL_PATH


def replace_file(target: Path, content: bytes) -> None:
    """Atomically replace a mirror entry without writing through hard links."""
    mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        temporary_path.chmod(mode)
        temporary_path.replace(target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def sync_skill(check: bool) -> int:
    canonical = {
        path.relative_to(SKILL_PATH): data
        for path, data in read_package(PACKAGE, ROOT).items()
        if path.is_relative_to(SKILL_PATH)
    }
    if MIRROR.resolve() != MIRROR:
        raise ValueError(f"Mirror must stay inside the checkout without symlinks: {MIRROR}")
    mirror = package_files(MIRROR, ROOT) if MIRROR.exists() else {}
    stale = mirror.keys() - canonical.keys()
    changed = {path for path, data in canonical.items() if mirror.get(path) != data}

    if check:
        for path in sorted(stale):
            print(f"Unexpected mirror file: {path.as_posix()}")
        for path in sorted(changed):
            print(f"Missing or out-of-date mirror file: {path.as_posix()}")
        if stale or changed:
            print("Run python scripts/sync_codex_skill.py to refresh the checkout skill.")
            return 1
    else:
        unmanaged = sorted(path.as_posix() for path in stale if not skill_file_allowed(path))
        if unmanaged:
            raise ValueError(f"Move unmanaged files out of the mirror: {', '.join(unmanaged)}")
        for path in stale:
            (MIRROR / path).unlink()
        for path in sorted(changed):
            target = MIRROR / path
            target.parent.mkdir(parents=True, exist_ok=True)
            replace_file(target, canonical[path])

    print(f"Checkout skill matches the portable source ({len(canonical)} files)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report differences without writing")
    args = parser.parse_args()
    try:
        return sync_skill(args.check)
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        parser.exit(1, f"Cannot sync Codex SEO: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
