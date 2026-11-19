#!/usr/bin/env python3
"""Check working-tree files for legacy product integration and crawler labels."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_NAME = "clau" "de"
LEGACY_PROJECT = f"{LEGACY_NAME}-seo"
LEGACY_AGENT_TOKEN = LEGACY_PROJECT.replace("-", "")
PRODUCT_REFERENCE = re.compile(
    rf"{LEGACY_NAME}[ -](?:code|desktop|seo|banana)|\b{LEGACY_AGENT_TOKEN}\b|\b{LEGACY_NAME}-blog\b|"
    rf"{LEGACY_NAME}_plugin_root|{LEGACY_NAME}_seo|\.{LEGACY_NAME}|"
    rf"\b{LEGACY_NAME}\s+(?:will|would|can|then|calls|uses|fills|acts)\b|"
    rf"\b(?:returned|generated|written) by {LEGACY_NAME}\b|\bfor {LEGACY_NAME} to\b",
    re.IGNORECASE,
)
UPSTREAM_URL = f"https://github.com/AgriciDaniel/{LEGACY_PROJECT}"
CRAWLERS = ("ClaudeBot", "Claude-SearchBot", "Claude-User")
PORTABLE_SKILLS = ("plugins/codex-seo/skills/seo", ".agents/skills/seo")
CRAWLER_FILES = (
    "scripts/agentic_check.py",
    "skills/seo-technical/SKILL.md",
    "skills/seo-geo/SKILL.md",
    *(f"{prefix}/references/topics/ai-crawler-access.md" for prefix in PORTABLE_SKILLS),
)
# Literals are limited to their provenance or crawler documentation files.
PROVENANCE = {
    "README.md": (UPSTREAM_URL, f"[AgriciDaniel/{LEGACY_PROJECT}]"),
    "CHANGELOG.md": (UPSTREAM_URL,),
    "CITATION.cff": (UPSTREAM_URL, f"title: {LEGACY_NAME.title()} SEO"),
    "CONTRIBUTORS.md": (UPSTREAM_URL, f"https://github.com/matej-marjanovic/{LEGACY_PROJECT}",
                        f"[matej-marjanovic/{LEGACY_PROJECT}]", f"Chriss54/{LEGACY_NAME}-blog-multilingual"),
    "docs/MIGRATION-v1-to-v2.md": (UPSTREAM_URL,),
    "docs/WORKFLOW-public-private.md": (UPSTREAM_URL,),
    "scripts/content_humanize.py": (f"ivankuznetsov/{LEGACY_PROJECT}",),
    "scripts/content_quality.py": (f"ivankuznetsov/{LEGACY_PROJECT}",),
    "skills/seo-agentic/references/lighthouse-agentic-category.md": (f"{LEGACY_PROJECT}.md",),
    "skills/seo-agentic/references/vendor-matrix.md": (f"https://{LEGACY_PROJECT}.md/", f"support.{LEGACY_NAME}.com"),
    "skills/seo-flow/references/flow-framework.md": (f"![{LEGACY_NAME.title()} SEO 10-principle methodology",),
    "tests/fixtures/lighthouse_agentic_13_5_psi.json": (f"https://{LEGACY_PROJECT}.md/", f"{LEGACY_NAME.title()} SEO"),
}
for prefix in PORTABLE_SKILLS:
    notices = f"{prefix}/references/notices"
    PROVENANCE[f"{notices}/CONTRIBUTORS.md"] = PROVENANCE["CONTRIBUTORS.md"]
    for name in ("attribution.md", "upstream-LICENSE.txt", "content-brief-LICENSE.txt"):
        PROVENANCE[f"{notices}/{name}"] = (UPSTREAM_URL,)
REMOVED_PACKAGING = (
    f".{LEGACY_NAME}-plugin",
    f"{LEGACY_NAME.upper()}.md",
    "install.sh", "install.ps1", "uninstall.sh", "uninstall.ps1",
    "hooks/hooks.json", "hooks/run-python-hook.js",
)


def _is_scannable_file(path: Path, root: Path) -> bool:
    """Only read regular files whose resolved path remains inside the checkout."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def main() -> int:
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode().split("\0")
    issues = [f"Obsolete packaging still present: {name}" for name in REMOVED_PACKAGING if (ROOT / name).exists()]
    for name in filter(None, paths):
        path = ROOT / name
        if not _is_scannable_file(path, ROOT):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError):
            continue
        allowed = PROVENANCE.get(name, ())
        if path.name in {"LICENSE", "LICENSE.txt"}:
            allowed += (UPSTREAM_URL, f"{LEGACY_NAME.title()} SEO")
        for line_no, line in enumerate(content.splitlines(), 1):
            for value in allowed:
                line = line.replace(value, "")
            if PRODUCT_REFERENCE.search(line):
                issues.append(f"{name}:{line_no}: {line.strip()}")
    for name in CRAWLER_FILES:
        path = ROOT / name
        if not _is_scannable_file(path, ROOT):
            issues.append(f"Required crawler guidance missing or unsafe: {name}")
            continue
        content = path.read_text(encoding="utf-8")
        for crawler in CRAWLERS:
            if not re.search(rf"\b{re.escape(crawler)}\b", content):
                issues.append(f"Retained crawler label {crawler} missing from {name}")
    if issues:
        print("\n".join(issues))
        return 1
    print("Codex product cleanup passed. Upstream notices and crawler labels are allowed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
