# Checkout and release workflow

The canonical repository is the independent public project [doofx0071/codex-seo](https://github.com/doofx0071/codex-seo). Its source history is carried forward from an earlier fork, and `main` is the release and contribution branch. Codex SEO is independently maintained and derived from [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo); preserve the upstream source attribution, MIT notices, and history as provenance.

1. Run the local checks in [Phase 1 verification](PHASE1-VERIFICATION.md).
2. After the plugin packaging is in place, sync the checkout skill and build the archive from the reviewed commit.
3. Record the source SHA and archive SHA-256 with the release or private distribution, then smoke-test the installed archive on ChatGPT Desktop and Codex.

Point the project homepage to its [Codex SEO README](https://github.com/doofx0071/codex-seo/tree/main#readme) and describe the repository as “SEO audit toolkit and portable plugin for Codex and ChatGPT.”

Use reviewed checkout source for local tooling and a built plugin archive for plugin distribution. Keep credentials, runtime caches, and audit output out of either release path.
