# Migrate to the Codex SEO checkout

1. Open a checkout of `helx0071/codex-seo` on `codex-native-support` in Codex. Follow [Installation](INSTALLATION.md).
2. Update automation and saved prompts to use `./scripts/codex-seo` from the checkout or its quoted absolute path from the audited project. Use `$seo audit <url>` and other skill prompts in Codex.
3. Run `./scripts/codex-seo doctor --json`. With user approval, run `./scripts/codex-seo setup` to create the managed environment for this checkout.
4. Keep existing audit folders in their original projects. Reconfigure credentials only for the integrations you need. Use a dedicated `CODEX_SEO_PROFILE_DIR` if you want a separate profile. Review [MCP and provider setup](MCP-INTEGRATION.md) before enabling providers.

The upstream release history and migration notes are available in the [source repository](https://github.com/AgriciDaniel/claude-seo).
