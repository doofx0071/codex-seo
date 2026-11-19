#!/usr/bin/env python3
"""Check local prerequisites for the Banana MCP server without a provider call."""

import argparse
import os
import shutil


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    checks = {
        "npx is available": shutil.which("npx") is not None,
        "GOOGLE_AI_API_KEY is set": bool(os.environ.get("GOOGLE_AI_API_KEY")),
    }
    for label, passed in checks.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")
    print("Confirm nanobanana-mcp is registered and connected in Codex.")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
