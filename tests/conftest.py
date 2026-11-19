"""Keeps the suite independent of the developer's own codex-seo profile.

Removed before pytest imports any test module: a rejected value would
otherwise stop the import of google_auth and abort collection.
"""

import os

os.environ.pop("CODEX_SEO_PROFILE_DIR", None)
