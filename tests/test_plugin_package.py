"""Portable plugin package checks (also runnable with standard-library unittest)."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plugins" / "codex-seo"
SKILL = PACKAGE / "skills" / "seo"
MIRROR = ROOT / ".agents" / "skills" / "seo"
SCRIPTS = ROOT / "scripts"


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def run_script(name: str, *args: str | Path, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / name), *map(str, args)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def copy_fixture(root: Path) -> None:
    shutil.copytree(PACKAGE, root / PACKAGE.relative_to(ROOT))
    (root / "scripts").mkdir()
    for name in ("build_plugin.py", "sync_codex_skill.py"):
        shutil.copy2(SCRIPTS / name, root / "scripts" / name)


def set_png_dimensions(path: Path, width: int, height: int) -> None:
    data = bytearray(path.read_bytes())
    data[16:24] = struct.pack(">II", width, height)
    data[29:33] = struct.pack(">I", zlib.crc32(b"IHDR" + data[16:29]) & 0xFFFFFFFF)
    path.write_bytes(data)


class TestPluginPackage(unittest.TestCase):
    def test_manifest_metadata_and_product_policy(self) -> None:
        manifest = json.loads((PACKAGE / "plugin.json").read_bytes())
        self.assertTrue({"skills", "mcpServers", "apps", "interface"}.isdisjoint(manifest))
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(manifest["name"], "codex-seo")
        self.assertEqual(manifest["version"], "0.1.2")
        self.assertEqual(set(manifest["extensions"]["com.openai"]), {"interface"})
        interface = manifest["extensions"]["com.openai"]["interface"]
        self.assertEqual(interface["displayName"], "Codex SEO")
        self.assertEqual(interface["category"], "Data & Analytics")
        self.assertEqual(interface["logo"], "./assets/logo.png")
        self.assertEqual(interface["composerIcon"], "./assets/composer-icon.png")
        self.assertEqual(
            interface["privacyPolicyURL"],
            "https://github.com/helx0071/codex-seo/blob/main/PRIVACY.md",
        )
        self.assertEqual(interface["supportURL"], "https://github.com/helx0071/codex-seo/issues")
        self.assertTrue(0 < len(interface["shortDescription"]) <= 30)

        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        for required_notice in (
            "Skills-only plugin privacy listing addendum", "Information and purpose", "Recipients",
            "Retention", "User controls", "https://github.com/helx0071/codex-seo/issues",
            "host-selected browsing or search provider", "accessed public site",
            "those services' terms apply",
        ):
            self.assertIn(required_notice, privacy)

        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        opening, frontmatter, body = skill_text.split("---", 2)
        self.assertEqual(opening, "")
        metadata = {}
        for line in frontmatter.strip().splitlines():
            field, value = line.split(": ", 1)
            metadata[field] = json.loads(value)  # Quoted JSON strings are valid YAML scalars.
        self.assertEqual(metadata["name"], "seo")
        self.assertTrue(metadata["description"].strip())
        self.assertTrue(body.strip())

        metadata = json.loads((SKILL / "agents" / "openai.yaml").read_bytes())
        self.assertEqual(set(metadata), {"interface", "policy"})
        self.assertEqual(metadata["interface"]["display_name"], "SEO")
        self.assertEqual(metadata["policy"], {"allow_implicit_invocation": True, "products": ["CHAT", "CODEX"]})

    def test_checkout_mirror_matches_every_canonical_skill_file(self) -> None:
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertEqual(snapshot(MIRROR), snapshot(SKILL))
        check = run_script("sync_codex_skill.py", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_guides_and_roles_match_checkout_inventory(self) -> None:
        guides = {path.parent.name for path in (ROOT / "skills").glob("seo-*/SKILL.md")}
        prompts = {path.stem for path in (ROOT / "agents").glob("seo-*.md")}
        refs = SKILL / "references"
        self.assertEqual(len(guides), 28)
        self.assertEqual(len(prompts), 20)
        self.assertEqual({path.stem for path in (refs / "guides").glob("*.md")}, guides)
        self.assertEqual({path.stem for path in (refs / "roles").glob("seo-*.md")}, prompts)
        self.assertEqual((refs / "notices" / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        self.assertEqual(
            (refs / "notices" / "CONTRIBUTORS.md").read_bytes(),
            (ROOT / "CONTRIBUTORS.md").read_bytes().replace(
                b"](CONTRIBUTING.md)", b"](https://github.com/helx0071/codex-seo/blob/HEAD/CONTRIBUTING.md)"
            ),
        )
        self.assertEqual(
            {path.read_bytes() for path in (refs / "notices").glob("*-LICENSE.txt")},
            {path.read_bytes() for path in (ROOT / "skills").glob("*/LICENSE.txt")},
        )

    def test_archive_is_one_standalone_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Codex SEO.zip"
            built = run_script("build_plugin.py", "--output", output)
            self.assertEqual(built.returncode, 0, built.stderr)
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
                self.assertEqual(
                    {name: archive.read(name) for name in archive.namelist()},
                    snapshot(PACKAGE),
                )
                self.assertEqual(
                    [name for name in archive.namelist() if name.endswith(("/SKILL.md", "plugin.json"))],
                    ["plugin.json", "skills/seo/SKILL.md"],
                )
                self.assertIn("assets/logo.png", archive.namelist())
                self.assertIn("assets/composer-icon.png", archive.namelist())
                self.assertTrue(all(not entry.is_dir() for entry in archive.infolist()))
            second = output.with_name("repeat.zip")
            rebuilt = run_script("build_plugin.py", "--output", second)
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            self.assertEqual(output.read_bytes(), second.read_bytes())

    def test_build_rejects_invalid_png_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            icon = root / PACKAGE.relative_to(ROOT) / "assets" / "logo.png"
            icon.write_bytes(b"not a png")
            output = root / "plugin.zip"
            built = run_script("build_plugin.py", "--output", output, root=root)
            self.assertNotEqual(built.returncode, 0)
            self.assertIn("PNG", built.stderr)

    def test_build_rejects_non_square_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            icon = root / PACKAGE.relative_to(ROOT) / "assets" / "logo.png"
            set_png_dimensions(icon, 1253, 1254)
            built = run_script("build_plugin.py", "--output", root / "plugin.zip", root=root)
            self.assertNotEqual(built.returncode, 0)
            self.assertIn("must be square", built.stderr)

    def test_build_rejects_undersized_logo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            icon = root / PACKAGE.relative_to(ROOT) / "assets" / "logo.png"
            set_png_dimensions(icon, 128, 128)
            built = run_script("build_plugin.py", "--output", root / "plugin.zip", root=root)
            self.assertNotEqual(built.returncode, 0)
            self.assertIn("dimensions out of range", built.stderr)

    def test_build_rejects_undersized_composer_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            icon = root / PACKAGE.relative_to(ROOT) / "assets" / "composer-icon.png"
            set_png_dimensions(icon, 32, 32)
            built = run_script("build_plugin.py", "--output", root / "plugin.zip", root=root)
            self.assertNotEqual(built.returncode, 0)
            self.assertIn("dimensions out of range", built.stderr)

    def test_build_rejects_uncontained_icon_paths(self) -> None:
        for field in ("logo", "composerIcon"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                copy_fixture(root)
                package = root / PACKAGE.relative_to(ROOT)
                manifest_path = package / "plugin.json"
                manifest = json.loads(manifest_path.read_bytes())
                manifest["extensions"]["com.openai"]["interface"][field] = "../logo.png"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                built = run_script("build_plugin.py", "--output", root / "plugin.zip", root=root)
                self.assertNotEqual(built.returncode, 0)
                self.assertIn("contained PNG package assets", built.stderr)

    def test_build_rejects_archive_inside_package(self) -> None:
        output = PACKAGE / "unexpected.zip"
        result = run_script("build_plugin.py", "--output", output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside", result.stderr)
        self.assertFalse(output.exists())

    def test_build_rejects_output_symlink_without_touching_referent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            referent = root / "keep.txt"
            referent.write_bytes(b"preserve this file")
            output = root / "codex-seo-plugin.zip"
            try:
                output.symlink_to(referent)
            except (NotImplementedError, OSError):
                self.skipTest("Creating symlinks requires OS support and privileges")
            result = run_script("build_plugin.py", "--output", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output symlink", result.stderr)
            self.assertEqual(referent.read_bytes(), b"preserve this file")
            self.assertTrue(output.is_symlink())

    def test_build_checks_inline_and_reference_style_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            skill = root / SKILL.relative_to(ROOT) / "SKILL.md"
            original = skill.read_bytes()
            output = root / "plugin.zip"

            skill.write_bytes(
                original
                + b"\n[Guide][guide]\n\n[guide]: references/guides/seo-agentic.md\n"
            )
            built = run_script("build_plugin.py", "--output", output, root=root)
            self.assertEqual(built.returncode, 0, built.stderr)

            skill.write_bytes(original + b"\n[sample]:\nHello world\n")
            output.unlink()
            built = run_script("build_plugin.py", "--output", output, root=root)
            self.assertEqual(built.returncode, 0, built.stderr)

            (root / "other.md").write_text("Outside the skill package.", encoding="utf-8")
            escaping_definitions = (
                b"\n[Outside][escape]\n\n[escape]: <../../../../other.md>\n",
                b"\r\n[Outside][escape]\r\n\r\n[escape]:\r\n  <../../../../other.md>\r\n",
                b"\n> [Outside][escape]\n>\n> [escape]:\n>   <../../../../other.md>\n",
                b"\n- [Outside][escape]\n\n- [escape]: ../../../../other.md\n",
                b"\n[Outside][escape]\n\n[escape]:\n../../../../other.md\n",
                b"\n[Outside](\n  ../../../../other.md\n)\n",
            )
            for definition in escaping_definitions:
                with self.subTest(definition=definition):
                    skill.write_bytes(original + definition)
                    output.unlink(missing_ok=True)
                    built = run_script("build_plugin.py", "--output", output, root=root)
                    self.assertNotEqual(built.returncode, 0)
                    self.assertIn("missing or uncontained reference", built.stderr)
                    self.assertFalse(output.exists())

    def test_build_rejects_missing_and_escaping_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            skill = root / SKILL.relative_to(ROOT) / "SKILL.md"
            original = skill.read_bytes()
            (root / "other.md").write_text("Outside the package.", encoding="utf-8")
            for link in ("references/missing.md", "../../../../other.md"):
                with self.subTest(link=link):
                    skill.write_bytes(original + f"\n[Invalid reference]({link})\n".encode())
                    output = root / "plugin.zip"
                    built = run_script("build_plugin.py", "--output", output, root=root)
                    self.assertNotEqual(built.returncode, 0)
                    self.assertIn("missing or uncontained reference", built.stderr)
                    self.assertFalse(output.exists())

    def test_build_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            reference = root / SKILL.relative_to(ROOT) / "references" / "linked.md"
            try:
                reference.symlink_to(ROOT / "README.md")
            except (NotImplementedError, OSError):
                self.skipTest("Creating symlinks requires OS support and privileges")
            output = root / "plugin.zip"
            result = run_script("build_plugin.py", "--output", output, root=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Symlink or uncontained path", result.stderr)
            self.assertFalse(output.exists())

    def test_sync_check_detects_drift_and_sync_repairs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            result = run_script("sync_codex_skill.py", root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            mirror = root / MIRROR.relative_to(ROOT)
            changed = mirror / "SKILL.md"
            changed.write_bytes(b"Changed.\n")
            stale = mirror / "references" / "outdated.md"
            stale.write_bytes(b"Stale.\n")
            result = run_script("sync_codex_skill.py", "--check", root=root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("Missing or out-of-date mirror file: SKILL.md", result.stdout)
            self.assertIn("Unexpected mirror file: references/outdated.md", result.stdout)
            self.assertEqual(changed.read_bytes(), b"Changed.\n")
            self.assertTrue(stale.exists())
            result = run_script("sync_codex_skill.py", root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(snapshot(mirror), snapshot(SKILL))

    def test_sync_replaces_hard_link_without_overwriting_its_referent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            result = run_script("sync_codex_skill.py", root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            mirror = root / MIRROR.relative_to(ROOT)
            target = mirror / "SKILL.md"
            referent = root / "unrelated.txt"
            referent.write_bytes(b"preserve this file")
            target.unlink()
            try:
                os.link(referent, target)
            except (NotImplementedError, OSError):
                self.skipTest("Creating hard links requires OS support and privileges")

            result = run_script("sync_codex_skill.py", root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(referent.read_bytes(), b"preserve this file")
            self.assertNotEqual(target.stat().st_ino, referent.stat().st_ino)
            self.assertEqual(target.read_bytes(), (SKILL / "SKILL.md").read_bytes())

    def test_reference_workflows_are_standalone(self) -> None:
        for path in (SKILL / "references").rglob("*.md"):
            if "notices" in path.relative_to(SKILL).parts:
                continue
            with self.subTest(path=path.relative_to(SKILL)):
                source = path.read_text(encoding="utf-8")
                for text in ("./scripts/", ".codex/agents/", "CODEX_SEO_PROFILE_DIR", "requires_local_executor"):
                    self.assertNotIn(text, source)
        workflow = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("apply the same prompts inline", workflow)
        self.assertIn("**unavailable**", workflow)
