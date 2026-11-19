# Codex SEO Phase 1 verification

## Workstation prerequisites

Use a checkout of `codex-native-support`, Git, Bash, and Python 3.11 through 3.14. On Windows use Git Bash or WSL with Python in the same environment. Windows PowerShell 5.1 or later can check the `.ps1` wrappers and needs Git Bash on `PATH` for execution. Use a workstation with package download access, and the ChatGPT Desktop and Codex surfaces that can access the private plugin. Provider credentials are optional and unnecessary for this smoke test.

## Local checkout checks

Create and activate a separate development virtual environment. On Unix or WSL:

```bash
python3 -m venv .venv-dev
source .venv-dev/bin/activate
pip install -r requirements.txt pytest
```

With Windows Git Bash, use `python -m venv .venv-dev` and `source .venv-dev/Scripts/activate` instead. Run these from the checkout root:

```bash
python scripts/check_codex_cleanup.py
python scripts/consistency_check.py --json
python scripts/portability_check.py --json
python -m unittest discover -s tests -p 'test_schema_validator_cli.py' -v
python -m unittest discover -s tests -p 'test_codex_cleanup.py' -v
python -m unittest discover -s tests -p 'test_plugin_package.py' -v
python -m pytest tests/test_codex_agent_configs.py tests/test_agent_mcp_permissions.py tests/test_sync_flow.py tests/test_shopify_crawl.py -q
python -m pytest tests/test_manifest_consistency.py tests/test_pyproject_metadata.py tests/test_hosted_plugin_layout.py tests/test_runtime_installers.py tests/test_manual_install_layout.py tests/test_extension_mirrors.py tests/test_extension_installer_injection.py tests/test_banana_install_layout.py tests/test_banana_key_masking.py tests/test_dataforseo_tool_names.py tests/test_consistency_check.py tests/test_portability.py tests/test_ai_crawler_claims.py -q
python -m pytest tests/ -v
```

The full suite can run with network tests disabled by leaving `CODEX_SEO_NETWORK_TESTS` unset. Checkout browser tests need installed Chromium and platform browser libraries. Test the normal managed runtime entry point separately:

```bash
./scripts/codex-seo setup
./scripts/codex-seo doctor --json
./scripts/codex-seo run seo_updates.py --limit 1 --json
./scripts/codex-seo run render_page.py https://example.com --mode auto --json
```

Expect `ready: true` after setup, one bundled update, and a response from a public sample page. The browser test requires network access and a functioning Chromium installation.

To test extension script discovery, use a clean checkout and no credentials. Run `./extensions/shopify/install.sh`, confirm `.agents/skills/seo-shopify/SKILL.md` points to the checkout guide, then run `./extensions/shopify/uninstall.sh`. In a disposable checkout, rename its directory after registration and verify that the relative link, repeat install, and uninstall still work. To test placeholder creation, run the install script with `--create-shopify-env` from a disposable audit directory using the quoted absolute path. Verify the placeholder goes in that directory and that rerunning never overwrites it. The PowerShell scripts with equivalents can be exercised the same way with Git Bash on `PATH`.

## Plugin package checks

Run these package checks from the checkout root.

```bash
python scripts/sync_codex_skill.py --check
python -m unittest discover -s tests -p test_plugin_package.py -v
python -m pytest tests/test_plugin_package.py -q
python scripts/build_plugin.py --output dist/codex-seo-plugin.zip
python -m zipfile -t dist/codex-seo-plugin.zip
python -m zipfile -l dist/codex-seo-plugin.zip
```

The build validates the root manifest as JSON, the skill frontmatter as YAML with quoted string values, and `agents/openai.yaml` as YAML in JSON syntax. Its Markdown scanner checks supported inline destinations and reference definitions, including destinations split across lines and common list/blockquote containers, for package containment and reachability. Review nonstandard Markdown extensions separately. The focused tests check plugin ID `codex-seo`, display name `Codex SEO`, initial version `0.1.0`, category `Data & Analytics`, `CHAT` and `CODEX` policy, checkout skill parity, and the contents of the built archive. If the mirror has drifted, run `python scripts/sync_codex_skill.py` and repeat the check. Use the following commands to record the source commit and archive SHA-256.

```bash
git rev-parse HEAD
python -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("dist/codex-seo-plugin.zip").read_bytes()).hexdigest())'
```

## Desktop smoke checks

1. Install the private build in ChatGPT Desktop. Start a new Chat or Work session with access to the plugin and without the checkout as the working folder. Ask “Use Codex SEO to audit https://example.com. Cite observable evidence, prioritize the fixes, and label unavailable measurements.”
2. In the desktop app's Codex surface, open a clean project with access to the plugin. Ask “Use the Codex SEO skill to review https://example.com for technical SEO and structured data. Keep the review read-only and tell me what you could verify.”
3. Confirm plugin discovery and invocation in both sessions. The answer should distinguish source observations from measured results and identify unavailable crawl, browser, analytics, or field Core Web Vitals evidence. It should avoid invented metrics, checkout-only commands, and provider calls.
4. Open the repository in a separate Codex session and ask `$seo audit https://example.com`. Confirm the checkout skill is discovered. If local tools and specialist agents are available, confirm that script-backed checks use the managed launcher and that the lead agent returns one coherent report.

## Task 2 verification record

- Passed the working-tree product cleanup audit. It checks tracked and untracked, nonignored files for product-specific integration remnants while retaining source provenance, legal notices, contributor references, and third-party crawler labels. Root and component license files are byte-for-byte unchanged.
- Passed the consistency and portability checks, Python syntax, Bash syntax, PowerShell ASCII, and parsing for tracked TOML, YAML, JSON, CFF, and SVG files. The consistency check reports an existing unreferenced-script warning for the Google properties helper.
- Passed 68 existing assertions directly, covering fixture-free checks and checks that need only a temporary directory. These checks ran without pytest.
- Passed offline launcher dispatch and install, repeat-install, and uninstall for all 11 extensions in a disposable checkout with an isolated runtime fixture. Verified Shopify placeholder creation, owner-only POSIX mode, and preservation of existing files and symlinks.
- Pending full and focused pytest suites. The environment has no pytest, and external dependency installation is unavailable here.
- The managed doctor ran and reported the runtime and browser unavailable. Managed runtime readiness, Chromium measurements, and native PowerShell execution remain pending.

### Residual product cleanup

- Moved the JSON-LD validator from the deleted lifecycle-hook directory to `scripts/validate_schema.py`. It is now an explicit-file standalone CLI with neutral text/JSON output, stable exit codes, and no host-event input or hook response envelope.
- Rebranded all runtime HTTP user-agent strings, including Shopify crawler robots matching, to Codex SEO. Retained actual third-party crawler names used by the SEO guidance.
- Replaced misleading image-generation labels with Nano Banana/Gemini language while preserving upstream source attribution. Removed two unused README SVGs with legacy marketplace/model claims.
- Changed Matomo setup to least-privilege View-only credentials, separating skill registration from credential setup and accurately describing POST-body token handling plus HTTPS recommendations.
- Removed obsolete Claude model/tool/turn-limit headers from 24 role prompts. Agent model settings are in native `.codex/agents/*.toml` files; updated the test contract and architecture guide. Role instructions and provider security boundaries remain in the Markdown prompts.
- Updated `scripts/check_codex_cleanup.py` to scan the current working tree, including untracked files, and narrow its product-name check so it does not reject valid Claude crawler/SEO facts.
- Passed `python scripts/check_codex_cleanup.py`, `python scripts/consistency_check.py --json` (0 errors; one existing unreferenced Google helper warning), `python scripts/portability_check.py --json` (40 skills; 0 errors/warnings), Python compilation for changed runtime/validator files, 7 schema-validator CLI tests, 4 scanner path tests, and 12 plugin-package tests through `unittest`.
- Ran 6 native Codex agent configuration checks, 8 provider-safety checks, 41 validator detection/policy/ReDoS assertions, and 25 existing schema-v2 assertions directly with Python; all passed. The Shopify user-agent literal and `RobotFileParser` matching passed a standard-library static check.
- `pytest` remains unavailable in this environment (`No module named pytest`) and was not installed. Run the documented full pytest commands on the workstation.
- `test_schema_graph_semantics.py` and the full `test_shopify_crawl.py` module could not import because this environment lacks BeautifulSoup, `requests`, and `lxml`. Run them with the workstation dependencies installed.

## Task 3 verification record

- Built and tested `dist/codex-seo-plugin.zip` with Python 3.12. The ZIP test passed and the listing showed 77 regular files. It contains a root `plugin.json`, one `skills/seo/SKILL.md` entrypoint, its agent metadata, 28 guide adaptations, 20 specialist prompts, 20 topic references, the specialist index, and attribution and license notices.
- Checked the archive's JSON manifest and YAML metadata, the 76-file mirror, reference containment and reachability, rejection of symlinks and out-of-scope links, and repeat builds. All 12 focused tests passed under `unittest`, including escaping reference-style links with LF, CRLF, multiline destinations and blockquotes, output symlinks, and hard-linked mirror files.
- The reviewed archive is 52,713 bytes with SHA-256 `0a8b93c2583c309a21e742c0b7e5ca3d0b5e5fe0299871d33a5a30d944f02dc8`.
- The focused pytest run stopped with `No module named pytest`. Run it on a workstation with the test dependencies. Private plugin creation is recorded in Task 4; desktop installation and invocation remain pending.

## Task 4 verification record

- Created one private personal plugin named `codex-seo`, version `0.1.0`, from the reviewed plugin archive. The plugin creator returned plugin ID `plugins_6aff1ef6b5b88191a1c5a3f68299b014` and release ID `pluginrel_6aff1efa696c8191b4576970898a7915` on 2026-11-19.
- Re-read the stored plugin metadata and file listing. It is `USER` scope and `PRIVATE`, with one SEO skill at `skills/seo/SKILL.md`, matching `CHAT` and `CODEX` invocation policy, and both plugin manifests present. The stored skill and metadata were checked against the package contents; all 77 expected files are present.
- Plugin link: <https://chatgpt.com/plugins/plugins_6aff1ef6b5b88191a1c5a3f68299b014>.
- ChatGPT Desktop installation/discovery/invocation and Codex Desktop skill invocation cannot be exercised from this environment. Run the Desktop smoke checks above after opening the plugin link in the target account. Record whether both surfaces discover and invoke the skill, plus any host-specific limitations. Do not treat plugin creation or manifest policy as proof that either desktop surface has been tested.

## Task 5 GitHub publication status

- The Phase 1 source and documentation are committed locally on `codex-native-support`. The worktree is clean. The branch is 10 commits ahead of remote `origin/codex-native-support` (remote head `36a91f4`).
- GitHub confirmed the repository is public, with default branch `main`, description `Codex-native SEO skills and agents, adapted from AgriciDaniel/claude-seo (MIT licensed).`, and no homepage URL. GitHub CLI is installed but not authenticated in this environment. `git push origin codex-native-support` failed because Git could not prompt for credentials; no GitHub branch ref or repository settings were changed.
- On the workstation, authenticate and push the prepared branch, then apply the approved repository metadata:

```bash
gh auth login
git push --set-upstream origin codex-native-support
gh repo edit helx0071/codex-seo \
  --default-branch codex-native-support \
  --description "SEO toolkit and plugin for Codex and ChatGPT, with evidence-backed audits and specialist agents." \
  --homepage "https://github.com/helx0071/codex-seo/tree/codex-native-support#readme"
```

- Verify the push and settings with `gh repo view helx0071/codex-seo --json defaultBranchRef,description,homepageUrl,url` and `git status --short --branch`.
- If transferring this checkout to a workstation before the GitHub push, use the supplied `codex-seo-phase1.bundle`:

```bash
git clone --branch codex-native-support /path/to/codex-seo-phase1.bundle codex-seo
cd codex-seo
git remote set-url origin https://github.com/helx0071/codex-seo.git
```
