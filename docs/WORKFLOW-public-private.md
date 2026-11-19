# Checkout and release workflow

Make and review changes on `codex-native-support` in [helx0071/codex-seo](https://github.com/helx0071/codex-seo). Keep the upstream history available for provenance. The [source repository](https://github.com/AgriciDaniel/claude-seo) is the reference for upstream releases and contribution history.

1. Run the local checks in [Phase 1 verification](PHASE1-VERIFICATION.md).
2. After the plugin packaging is in place, sync the checkout skill and build the archive from the reviewed commit.
3. Record the source SHA and archive SHA-256 with the release or private distribution, then smoke-test the installed archive on ChatGPT Desktop and Codex.

When publishing the reviewed branch, point the fork homepage to its [Codex SEO README](https://github.com/helx0071/codex-seo/tree/codex-native-support#readme) and describe the repository as “SEO audit toolkit and portable plugin for Codex and ChatGPT.”

Use reviewed checkout source for local tooling and a built plugin archive for plugin distribution. Keep credentials, runtime caches, and audit output out of either release path.
