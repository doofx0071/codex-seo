#!/usr/bin/env python3
"""Run a standalone JSON-LD preflight on a local HTML-like source file.

Run `python scripts/validate_schema.py path/to/file.html` from the checkout.
This validator is not automatically attached to Codex edits. Critical findings
use exit status 2; advisory findings use exit status 0 and can be printed as
plain text or structured JSON with `--json`.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, List

BRACKET_PLACEHOLDERS = (
    "[Business Name]",
    "[City]",
    "[State]",
    "[Phone]",
    "[Address]",
    "[Your",
    "[INSERT",
    "[URL]",
    "[Email]",
)
BARE_PLACEHOLDER_RE = re.compile(r"\bREPLACE(?:_[A-Z]+)*\b")

# Match every <script ...>...</script> pair, then filter on the type attribute.
# The previous pattern required ``type`` to be the first and only attribute, so
# blocks carrying a CSP ``nonce``, an ``id`` or ``data-*`` attributes, or an
# unquoted type value were skipped without validation.
#
# The attribute group is a small tokenizer, not a plain ``[^>]*``: it consumes a
# double-quoted value, a single-quoted value, or a run of characters that is
# neither a quote nor ``>``. A ``[^>]*`` scan ends the tag at the first ``>`` it
# sees, quoted or not, so an attribute value containing ``>`` (``data-cond="a>b"``,
# a templated nonce) truncated the tag early and fed the remainder of the
# attributes plus the real body to the JSON parser as garbage. Treating a quoted
# span as atomic keeps an embedded ``>`` from ending the tag prematurely.
# The fallback class excludes both quote characters: if it matched an
# apostrophe, the alternation would be ambiguous and a tag with many
# apostrophes and no closing tag would backtrack exponentially, hanging the
# standalone validator.
_ATTRS_RE = r'(?:"[^"]*"|\'[^\']*\'|[^"\'>])*'
SCRIPT_TAG_RE = re.compile(
    r"<script\b(" + _ATTRS_RE + r")>(.*?)</script\s*>", re.DOTALL | re.IGNORECASE
)
LD_JSON_TYPE_RE = re.compile(
    r"""(?:^|\s)type\s*=\s*"""
    r"""(?:"application/ld\+json"|'application/ld\+json'|application/ld\+json(?=\s|$))""",
    re.IGNORECASE,
)

# Server- or client-side template expressions that render JSON-LD at runtime.
# The CLI can inspect .jsx/.tsx/.vue/.svelte/.php/.ejs sources, where the script
# body is frequently an expression rather than literal JSON. Those blocks cannot
# be validated statically and must not be reported as invalid JSON.
SERVER_TEMPLATE_RE = re.compile(
    r"""^(?:
        <\?(?:php\b|=)            # <?php ... ?> / <?= ... ?>
      | <%                        # EJS / ERB
    )""",
    re.VERBOSE,
)
COMPONENT_EXPRESSION_RE = re.compile(
    r"""^(?:
        \{\{                      # Vue / Handlebars / Twig
      | \{@html\b                 # Svelte
      | \$\{                      # JS template literal
      | \{\s*[A-Za-z_$][\w$.]*    # JSX expression: {schema} / {JSON.stringify(...)}
    )""",
    re.VERBOSE,
)
COMPONENT_EXTENSIONS = (".jsx", ".tsx", ".vue", ".svelte")

SCHEMA_ORG_CONTEXTS = frozenset(
    {"https://schema.org", "http://schema.org", "https://schema.org/", "http://schema.org/"}
)


def _configure_utf8() -> None:
    """Keep validator diagnostics printable on legacy Windows console encodings."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def _extract_ld_json_blocks(content: str) -> List[str]:
    """Return the bodies of every ``<script type="application/ld+json">`` block.

    Attribute order, extra attributes (``nonce``, ``id``, ``data-*``), tag case
    and unquoted type values are all accepted; only the type value is decisive.
    """
    blocks = []
    for attributes, body in SCRIPT_TAG_RE.findall(content):
        if LD_JSON_TYPE_RE.search(attributes):
            blocks.append(body)
    return blocks


def _is_template_expression(block: str, filepath: str = "") -> bool:
    """True when the script body is rendered at runtime rather than literal JSON.

    Server-side markers (PHP, EJS) are never valid JSON and are skipped for
    every file type. Component expressions (JSX, Vue, Svelte, template
    literals) are only skipped in component sources, so a malformed object
    literal in a plain ``.html`` file is still reported.
    """
    if SERVER_TEMPLATE_RE.match(block):
        return True
    if filepath.lower().endswith(COMPONENT_EXTENSIONS):
        return bool(COMPONENT_EXPRESSION_RE.match(block))
    return False


def _is_schema_org_context(value: Any) -> bool:
    """Accept the schema.org context in its string, list and object forms."""
    if isinstance(value, str):
        return value in SCHEMA_ORG_CONTEXTS
    if isinstance(value, list):
        return any(_is_schema_org_context(item) for item in value)
    if isinstance(value, dict):
        return _is_schema_org_context(value.get("@vocab"))
    return False


def validate_jsonld(content: str, filepath: str = "") -> List[str]:
    """Validate JSON-LD blocks in HTML content."""
    errors = []
    blocks = _extract_ld_json_blocks(content)

    if not blocks:
        return []  # No schema found; not an error

    for i, block in enumerate(blocks, 1):
        block = block.strip()
        if _is_template_expression(block, filepath):
            continue  # Rendered at runtime; nothing to validate statically
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            errors.append(f"Block {i}: Invalid JSON; {e}")
            continue

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    errors.extend(_validate_schema_object(item, i))
                else:
                    errors.append(f"Block {i}: JSON-LD list members must be objects")
        elif isinstance(data, dict):
            errors.extend(_validate_schema_object(data, i))
        else:
            errors.append(f"Block {i}: JSON-LD root must be an object or list")

    return errors


def _validate_schema_object(
    obj: dict[str, Any], block_num: int, *, inherited_context: bool = False
) -> List[str]:
    """Validate one schema node, including members of a top-level ``@graph``.

    ``obj`` is the JSON-LD node and ``block_num`` is the script block number
    used in diagnostics. ``inherited_context`` is set for a node that takes its
    context from an enclosing graph. Returns the errors and warnings for the
    node and its graph members.
    """
    errors = []
    prefix = f"Block {block_num}"

    # Check @context
    if "@context" not in obj and not inherited_context:
        errors.append(f"{prefix}: Missing @context")
    elif "@context" in obj and not _is_schema_org_context(obj["@context"]):
        errors.append(f"{prefix}: @context should be 'https://schema.org'")

    graph = obj.get("@graph")
    has_graph = isinstance(graph, (dict, list))

    # A graph container does not need its own @type. Its object members do.
    if "@type" not in obj and not has_graph:
        errors.append(f"{prefix}: Missing @type")

    # Check for placeholder text
    placeholder_scope = {key: value for key, value in obj.items() if key != "@graph"}
    text = json.dumps(placeholder_scope, ensure_ascii=False)
    for p in BRACKET_PLACEHOLDERS:
        if p.lower() in text.lower():
            errors.append(f"{prefix}: Contains placeholder text: {p}")
    for placeholder in BARE_PLACEHOLDER_RE.findall(text):
        errors.append(f"{prefix}: Contains placeholder text: {placeholder}")

    # Schema.org permits multiple string values, but malformed values must not
    # disappear silently before type-specific checks run.
    raw_schema_type = obj.get("@type")
    schema_types = raw_schema_type if isinstance(raw_schema_type, list) else [raw_schema_type]
    if "@type" in obj and (
        not schema_types
        or any(not isinstance(schema_type, str) or not schema_type.strip() for schema_type in schema_types)
    ):
        errors.append(
            f"{prefix}: @type must be a non-empty string or a non-empty list of non-empty strings"
        )
    # dict.fromkeys drops repeats and keeps order, so ["HowTo", "HowTo"] is
    # reported once.
    schema_types = list(
        dict.fromkeys(
            schema_type
            for schema_type in schema_types
            if isinstance(schema_type, str) and schema_type.strip()
        )
    )
    deprecated = {
        "HowTo": "deprecated September 2023",
        "SpecialAnnouncement": "deprecated July 31, 2025",
        "CourseInfo": "retired June 2025",
        "EstimatedSalary": "retired June 2025",
        "LearningVideo": "retired June 2025",
        "ClaimReview": "retired June 2025; fact-check rich results discontinued",
        "VehicleListing": "retired June 2025; vehicle listing structured data discontinued",
    }
    for schema_type in schema_types:
        if schema_type in deprecated:
            errors.append(f"{prefix}: @type '{schema_type}' is {deprecated[schema_type]}")

    # Check for restricted types used incorrectly.
    # FAQPage is intentionally NOT flagged: Google retired FAQ rich results for
    # all sites (May 7, 2026), but FAQPage remains a valid Schema.org type.
    # This project makes no claim of a confirmed AI or ranking benefit.
    restricted: dict = {}
    for schema_type in schema_types:
        if schema_type in restricted:
            errors.append(
                f"{prefix}: @type '{schema_type}' is {restricted[schema_type]}; verify site qualifies"
            )

    if "@graph" in obj:
        if not has_graph:
            errors.append(f"{prefix}: @graph must be an object or list")
        else:
            context_is_inherited = inherited_context or "@context" in obj
            members = [graph] if isinstance(graph, dict) else graph
            for index, item in enumerate(members, 1):
                if not isinstance(item, dict):
                    errors.append(
                        f"{prefix}: @graph member {index} must be an object"
                    )
                    continue
                errors.extend(
                    _validate_schema_object(
                        item,
                        block_num,
                        inherited_context=context_is_inherited,
                    )
                )

    return errors


def _input_error(filepath: str, message: str, json_mode: bool) -> int:
    """Report why this explicit input could not be validated."""
    if json_mode:
        print(json.dumps({"file": filepath, "error": message}), file=sys.stderr)
    else:
        print(f"Schema validation could not run for {filepath}: {message}", file=sys.stderr)
    return 1


def main() -> int:
    _configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="HTML-like file to inspect")
    parser.add_argument("--json", action="store_true", help="Print findings as JSON")
    args = parser.parse_args()
    filepath = args.file

    if not os.path.isfile(filepath):
        parser.error(f"file does not exist or is not a regular file: {filepath}")

    # Only validate HTML-like files
    valid_extensions = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".php", ".ejs")
    if not filepath.lower().endswith(valid_extensions):
        return _input_error(
            filepath,
            f"unsupported file type; expected one of: {', '.join(valid_extensions)}",
            args.json,
        )

    # File-size guard: skip files >10MB to bound memory + CLI latency.
    # Real source files almost never exceed this; bigger inputs are typically
    # generated, minified bundles or accidental binary writes.
    MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MiB
    try:
        size = os.path.getsize(filepath)
    except OSError as exc:
        return _input_error(filepath, f"cannot inspect file size: {exc}", args.json)
    if size > MAX_FILE_BYTES:
        return _input_error(
            filepath,
            f"file exceeds the {MAX_FILE_BYTES}-byte validation limit",
            args.json,
        )

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as exc:
        return _input_error(filepath, f"cannot read file: {exc}", args.json)

    errors = validate_jsonld(content, filepath)

    if not errors:
        return 0

    # Categorize errors
    critical_keywords = ["placeholder", "deprecated", "retired"]
    critical = [e for e in errors if any(kw in e.lower() for kw in critical_keywords)]
    warnings = [e for e in errors if e not in critical]

    if critical:
        # Exit 2 flags critical errors on stderr.
        if args.json:
            print(json.dumps({"file": filepath, "errors": critical, "warnings": warnings}), file=sys.stderr)
        else:
            print("Schema validation errors (fix before shipping):", file=sys.stderr)
            for error in critical:
                print(f"  - {error}", file=sys.stderr)
            if warnings:
                print("Also warnings:", file=sys.stderr)
                for warning in warnings:
                    print(f"  - {warning}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"file": filepath, "warnings": warnings}))
    else:
        print(f"Schema validation warnings for {filepath}:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
