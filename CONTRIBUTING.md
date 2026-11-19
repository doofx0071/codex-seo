# Contributing to Codex SEO

Report reproducible bugs in [GitHub Issues](https://github.com/helx0071/codex-seo/issues). Include your Codex or ChatGPT surface, the checkout commit or plugin version, the minimal prompt or command, and the expected and observed behavior. Remove credentials and private audit data from logs. Follow [SECURITY.md](SECURITY.md) for a vulnerability report.

## Development

Fork the repository and branch from `codex-native-support`. Run the checks in [Phase 1 verification](docs/PHASE1-VERIFICATION.md) from your checkout. Follow the [Code of Conduct](CODE_OF_CONDUCT.md) in project discussions.

- Put project skill entry points in `.agents/skills/` and shared workflow detail in `skills/`.
- Define Codex specialist roles in `.codex/agents/` and keep reusable prompts in `agents/`.
- Put deterministic checkout tools in `scripts/` and use `./scripts/codex-seo run` in their usage instructions.
- Keep optional provider setup in `extensions/` and make requests read-only unless the user explicitly authorizes a write.
- Preserve MIT notices, contributor credits, upstream source references and SEO crawler records.

Open a pull request against `codex-native-support` with a concise description and the checks you ran. Use mock or public fixtures and report checks you could not run.
