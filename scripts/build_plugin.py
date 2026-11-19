#!/usr/bin/env python3
"""Validate and build the standalone, skills-only Codex SEO plugin."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plugins" / "codex-seo"
SKILL_PATH = Path("skills/seo")
SKILL_FILES = {Path("SKILL.md"), Path("agents/openai.yaml")}
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MARKDOWN_LINK = re.compile(
    r"\]\(\s*(?:<([^>\n]+)>|([^\s)]+))"
    r"(?:[ \t\n]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\)\n]*\)))?[ \t\n]*\)",
    re.S,
)
REFERENCE_DEFINITION = re.compile(
    r"(?m)^(?:[ \t]{0,3}(?:>[ \t]?|(?:[-+*]|\d{1,9}[.)])[ \t]+))*"
    r"[ \t]{0,3}\[[^\]\n]+\]:[ \t]*"
    r"(?:\n(?:[ \t]{0,3}(?:>[ \t]?|(?:[-+*]|\d{1,9}[.)])[ \t]+))*[ \t]{0,4})?"
    r"(?:<([^>\n]+)>|(\S+))"
    r"(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\)\n]*\)))?[ \t]*$"
)
SAFE_COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")


def package_files(root: Path, boundary: Path) -> dict[Path, bytes]:
    """Read regular files with portable paths and reject symlinks in the tree."""
    if root.resolve() != root or not root.is_relative_to(boundary):
        raise ValueError(f"Directory must stay inside {boundary} without symlinks: {root}")
    if not root.is_dir():
        raise ValueError(f"Missing directory: {root}")

    files = {}
    seen = set()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Symlink or uncontained path: {path}")
        if any(not SAFE_COMPONENT.fullmatch(part) or part.endswith(".") for part in relative.parts):
            raise ValueError(f"Invalid package path: {relative.as_posix()}")
        casefolded = relative.as_posix().casefold()
        if casefolded in seen:
            raise ValueError(f"Case-insensitive path collision: {relative.as_posix()}")
        seen.add(casefolded)
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Expected a regular file: {path}")
        files[relative] = path.read_bytes()
    return files


def skill_file_allowed(relative: Path) -> bool:
    """The skill contains its entrypoint, metadata and text references."""
    return relative in SKILL_FILES or (
        relative.parts[0] == "references"
        and relative.name not in {"SKILL.md", "plugin.json"}
        and (relative.suffix in {".md", ".txt"} or relative == Path("references/notices/LICENSE"))
    )


def skill_frontmatter(source: bytes) -> dict[str, str]:
    """Parse the skill's YAML mapping of JSON-quoted string values."""
    text = source.decode("utf-8").replace("\r\n", "\n")
    opening, separator, rest = text.partition("\n")
    frontmatter, closing, body = rest.partition("\n---\n")
    if opening != "---" or not separator or not closing or not body.strip():
        raise ValueError("SKILL.md must contain YAML frontmatter and a workflow")
    fields = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(": ")
        if key not in {"name", "description"} or not separator or key in fields:
            raise ValueError(f"Invalid SKILL.md frontmatter: {line}")
        fields[key] = json.loads(value)
    return fields


def require_text(mapping: dict, *fields: str) -> None:
    for field in fields:
        value = mapping.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Expected a nonblank string for {field}")


def validate_metadata(manifest_bytes: bytes, skill_files: dict[Path, bytes]) -> None:
    manifest = json.loads(manifest_bytes)
    if set(manifest) != {
        "$schema", "name", "version", "description", "author", "repository",
        "license", "keywords", "extensions",
    } or (manifest["$schema"], manifest["name"], manifest["version"]) != (SCHEMA, "codex-seo", "0.1.0"):
        raise ValueError("Invalid Phase 1 plugin manifest")
    require_text(manifest, "description", "repository", "license")
    require_text(manifest["author"], "name")
    if not isinstance(manifest["keywords"], list) or any(
        not isinstance(value, str) or not value.strip() for value in manifest["keywords"]
    ):
        raise ValueError("Plugin keywords must be a list of nonblank strings")
    extensions = manifest["extensions"]
    if set(extensions) != {"com.openai"} or set(extensions["com.openai"]) != {"interface"}:
        raise ValueError("Phase 1 adds only OpenAI interface metadata")
    interface = extensions["com.openai"]["interface"]
    if set(interface) != {
        "displayName", "shortDescription", "longDescription", "developerName", "category", "defaultPrompt",
    }:
        raise ValueError("Unexpected OpenAI interface fields")
    require_text(interface, *interface)
    if interface["displayName"] != "Codex SEO" or interface["category"] != "Data & Analytics":
        raise ValueError("Unexpected plugin display name or category")
    if len(interface["shortDescription"]) > 30:
        raise ValueError("Plugin short description must be at most 30 characters")

    skill = skill_files[Path("SKILL.md")]
    if len(skill) > 1024**2:
        raise ValueError("SKILL.md exceeds 1 MiB")
    frontmatter = skill_frontmatter(skill)
    require_text(frontmatter, "name", "description")
    if frontmatter["name"] != "seo":
        raise ValueError("The SEO skill name must match its directory")

    metadata = json.loads(skill_files[Path("agents/openai.yaml")])
    if set(metadata) != {"interface", "policy"} or set(metadata["interface"]) != {
        "display_name", "short_description", "default_prompt",
    }:
        raise ValueError("Unexpected skill metadata fields")
    require_text(metadata["interface"], *metadata["interface"])
    policy = metadata["policy"]
    if (set(policy) != {"allow_implicit_invocation", "products"}
            or policy["allow_implicit_invocation"] is not True
            or policy["products"] != ["CHAT", "CODEX"]):
        raise ValueError("The SEO skill must allow implicit invocation in CHAT and CODEX")


def validate_references(skill_root: Path, files: dict[Path, bytes]) -> None:
    """Check supported Markdown link destinations and require local references to be reachable."""
    visited = set()
    pending = [Path("SKILL.md")]
    while pending:
        relative = pending.pop()
        if relative in visited:
            continue
        visited.add(relative)
        if relative.suffix != ".md":
            continue
        source = files[relative].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        links = [angle or bare for angle, bare in MARKDOWN_LINK.findall(source)]
        # Reference definitions are link destinations too. Check every definition,
        # whether or not the current Markdown parser finds a matching use.
        links.extend(
            angle or bare
            for angle, bare in REFERENCE_DEFINITION.findall(source)
        )
        for link in links:
            url = urlsplit(link.strip("<>"))
            if url.scheme in {"https", "http", "mailto"}:
                continue
            if url.scheme or url.netloc or url.path.startswith("/"):
                raise ValueError(f"{relative}: expected a relative link: {link}")
            if not url.path:
                continue
            path = unquote(url.path)
            if "\\" in path or Path(path).is_absolute():
                raise ValueError(f"{relative}: nonportable link: {link}")
            target = (skill_root / relative.parent / path).resolve()
            if not target.is_relative_to(skill_root) or target.relative_to(skill_root) not in files:
                raise ValueError(f"{relative}: missing or uncontained reference: {link}")
            pending.append(target.relative_to(skill_root))

    unused = sorted(path.as_posix() for path in files.keys() - visited - SKILL_FILES)
    if unused:
        raise ValueError(f"Unreferenced plugin files: {', '.join(unused)}")


def read_package(package: Path, boundary: Path) -> dict[Path, bytes]:
    files = package_files(package, boundary)
    manifest = files.get(Path("plugin.json"))
    skill_files = {
        path.relative_to(SKILL_PATH): data
        for path, data in files.items()
        if path.is_relative_to(SKILL_PATH)
    }
    if manifest is None or not SKILL_FILES <= skill_files.keys():
        raise ValueError("Package needs a root plugin.json, one SEO skill and agents/openai.yaml")
    if len(files) != len(skill_files) + 1 or not all(map(skill_file_allowed, skill_files)):
        raise ValueError("Unexpected files in the skills-only plugin")
    validate_metadata(manifest, skill_files)
    validate_references(package / SKILL_PATH, skill_files)
    return files


def write_archive(output: Path, files: dict[Path, bytes]) -> None:
    """Write a reproducible ZIP and keep a previous archive if a build fails."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, suffix=".tmp", delete=False) as temp:
        temporary_path = Path(temp.name)
    try:
        with ZipFile(temporary_path, "w") as archive:
            for path, payload in sorted(files.items(), key=lambda item: item[0].as_posix()):
                entry = ZipInfo(path.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        # Resolve the parent so a symlinked directory cannot redirect the build,
        # but preserve the final name so replacement never follows an output symlink.
        if args.output.is_symlink():
            raise ValueError("Refusing to write through an output symlink")
        output = args.output.parent.resolve() / args.output.name
        if output.is_relative_to(PACKAGE.resolve()):
            raise ValueError("Write the ZIP outside the packaged directory")
        files = read_package(PACKAGE, ROOT)
        write_archive(output, files)
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        parser.exit(1, f"Cannot build Codex SEO: {exc}\n")

    print(f"Built {args.output} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
