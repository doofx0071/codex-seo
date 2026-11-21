#!/usr/bin/env python3
"""Validate and build the standalone, skills-only Codex SEO plugin."""

from __future__ import annotations

import argparse
import json
import re
import struct
import zlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plugins" / "codex-seo"
SKILL_PATH = Path("skills/seo")
SKILL_FILES = {Path("SKILL.md"), Path("agents/openai.yaml")}
ICON_FILES = {Path("assets/logo.png"), Path("assets/composer-icon.png")}
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


def validate_png(path: Path, data: bytes, minimum_size: int) -> None:
    """Validate a complete square PNG icon against public package limits."""
    if len(data) > 5 * 1024 * 1024:
        raise ValueError(f"PNG icon exceeds 5 MiB: {path.as_posix()}")
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Expected PNG image: {path.as_posix()}")
    cursor = 8
    width = height = None
    found_idat = found_iend = False
    while cursor + 12 <= len(data):
        length = struct.unpack_from(">I", data, cursor)[0]
        chunk_type = data[cursor + 4:cursor + 8]
        chunk_end = cursor + 12 + length
        if chunk_end > len(data):
            raise ValueError(f"Truncated PNG image: {path.as_posix()}")
        chunk_data = data[cursor + 8:cursor + 8 + length]
        expected_crc = struct.unpack_from(">I", data, cursor + 8 + length)[0]
        if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != expected_crc:
            raise ValueError(f"Invalid PNG chunk checksum: {path.as_posix()}")
        if cursor == 8:
            if chunk_type != b"IHDR" or length != 13:
                raise ValueError(f"Invalid PNG header: {path.as_posix()}")
            width, height = struct.unpack_from(">II", chunk_data)
        elif chunk_type == b"IDAT":
            found_idat = True
        elif chunk_type == b"IEND":
            if length != 0:
                raise ValueError(f"Invalid PNG end chunk: {path.as_posix()}")
            found_iend = True
            cursor = chunk_end
            break
        cursor = chunk_end
    if not found_idat or not found_iend or cursor != len(data):
        raise ValueError(f"Incomplete PNG image: {path.as_posix()}")
    if width is None or height is None or width != height:
        raise ValueError(f"PNG icon must be square: {path.as_posix()}")
    if width < minimum_size or width > 4096:
        raise ValueError(f"PNG icon dimensions out of range: {path.as_posix()}")


def validate_metadata(manifest_bytes: bytes, skill_files: dict[Path, bytes]) -> None:
    manifest = json.loads(manifest_bytes)
    if set(manifest) != {
        "$schema", "name", "version", "description", "author", "repository",
        "license", "keywords", "extensions",
    } or (manifest["$schema"], manifest["name"], manifest["version"]) != (SCHEMA, "codex-seo", "0.1.2"):
        raise ValueError("Invalid Codex SEO 0.1.2 plugin manifest")
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
        "privacyPolicyURL", "supportURL", "logo", "composerIcon",
    }:
        raise ValueError("Expected the documented OpenAI privacy policy URL field")
    require_text(interface, *interface)
    if interface["privacyPolicyURL"] != "https://github.com/doofx0071/codex-seo/blob/main/PRIVACY.md":
        raise ValueError("Unexpected OpenAI privacy policy URL")
    if interface["supportURL"] != "https://github.com/doofx0071/codex-seo/issues":
        raise ValueError("Unexpected OpenAI support URL")
    if interface["logo"] != "./assets/logo.png" or interface["composerIcon"] != "./assets/composer-icon.png":
        raise ValueError("OpenAI logo and composer icon must use the contained PNG package assets")
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
    expected_files = {Path("plugin.json"), *(SKILL_PATH / path for path in skill_files), *ICON_FILES}
    if manifest is None or not SKILL_FILES <= skill_files.keys():
        raise ValueError("Package needs a root plugin.json, one SEO skill and agents/openai.yaml")
    if set(files) != expected_files or not all(map(skill_file_allowed, skill_files)):
        raise ValueError("Unexpected files in the skills-only plugin or a required icon is missing")
    validate_metadata(manifest, skill_files)
    for relative, minimum_size in ((Path("assets/logo.png"), 256), (Path("assets/composer-icon.png"), 48)):
        validate_png(relative, files[relative], minimum_size)
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
