#!/usr/bin/env bash
set -euo pipefail

source_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec "${source_dir}/../../scripts/codex-seo" run extension_install.py install "${source_dir##*/}" "$@"
