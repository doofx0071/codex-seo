# Codex SEO Phase 1 verification

## Workstation prerequisites

After the current release review merges, use a checkout of `main`, Git, Bash, and Python 3.11 through 3.14. The current review is prepared from `codex-native-support`; use that branch when checking its pull request. On Windows use Git Bash or WSL with Python in the same environment. Windows PowerShell 5.1 or later can check the `.ps1` wrappers and needs Git Bash on `PATH` for execution. Use a workstation with package download access, and the ChatGPT Desktop and Codex surfaces that can access the private plugin. Provider credentials are optional and unnecessary for this smoke test.

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

The build validates the root manifest as JSON, the skill frontmatter as YAML with quoted string values, and `agents/openai.yaml` as YAML in JSON syntax. Its Markdown scanner checks supported inline destinations and reference definitions, including destinations split across lines and common list/blockquote containers, for package containment and reachability. Review nonstandard Markdown extensions separately. The focused tests check plugin ID `codex-seo`, display name `Codex SEO`, candidate version `0.1.2`, category `Data & Analytics`, `CHAT` and `CODEX` policy, checkout skill parity, and the contents of the built archive. If the mirror has drifted, run `python scripts/sync_codex_skill.py` and repeat the check. Use the following commands to record the source commit and archive SHA-256.

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

- Published the complete Phase 1 source tree to the public `helx0071/codex-seo` repository on `codex-native-support`. GitHub's stored tree hash matched the prepared local `HEAD` tree before this publication record was added.
- The GitHub connector created one consolidated snapshot commit on top of the previous remote head because Git CLI authentication was unavailable. The earlier 10-commit local sequence is retained on the local `codex-native-support-local-history` backup branch; the published source tree contains the same code and documentation state.
- Changed the repository default branch from `main` to `codex-native-support`, set its description to `SEO toolkit and plugin for Codex and ChatGPT, with evidence-backed audits and specialist agents.`, and set its homepage to `https://github.com/helx0071/codex-seo/tree/codex-native-support#readme`. Verified these values through GitHub's repository API and settings page.
- Clone the published branch on a workstation:

```bash
git clone --branch codex-native-support https://github.com/helx0071/codex-seo.git
cd codex-seo
```

- For future local commits, authenticate the GitHub CLI or Git credential manager on the workstation, then push normally. Verify with `git status --short --branch` and `gh repo view helx0071/codex-seo --json defaultBranchRef,description,homepageUrl,url`.

## Workstation verification record (2026-11-20, P1-QA-02)

This record supplements the earlier environment-limited Task 2 and Task 3 entries above. The checkout was `C:\dev\codex-seo`, branch `codex-native-support`, at base commit `f321d581fe4dd546d025ad28e2f5c311d14846d0`; it was clean before verification. Commands below ran with actual Git Bash at `C:\Program Files\Git\bin\bash.exe` and Codex-bundled Python 3.12.14 added to PATH. A separate WindowsApps `bash` alias opened WSL, where Python was unavailable. That was an environment-selection issue, not a failure of the Git Bash launcher. The documented PowerShell wrapper initially could not find Python; it passed after adding `.venv-dev/Scripts` and Git Bash to PATH.

### Environment and checkout checks

- `python -m venv .venv-dev`: passed.
- `source .venv-dev/Scripts/activate`: passed in Git Bash.
- `pip install -r requirements.txt pytest`: exit 0; pytest 9.2.0 available.
- `python scripts/check_codex_cleanup.py`: passed.
- `python scripts/consistency_check.py --json`: exit 0; 740 files, 0 errors; one existing warning that `scripts/google_properties.py` is not referenced outside itself.
- `python scripts/portability_check.py --json`: exit 0; 40 skills, 0 errors and warnings.
- `python -m unittest discover -s tests -p 'test_schema_validator_cli.py' -v`: 7 passed.
- `python -m unittest discover -s tests -p 'test_codex_cleanup.py' -v`: 1 passed, 3 skipped because Windows symlink privileges were unavailable.
- `python -m unittest discover -s tests -p 'test_plugin_package.py' -v`: 10 passed, 2 skipped.
- `python -m pytest tests/test_codex_agent_configs.py tests/test_agent_mcp_permissions.py tests/test_sync_flow.py tests/test_shopify_crawl.py -q`: 71 passed, 3 skipped.
- `python -m pytest tests/test_manifest_consistency.py tests/test_pyproject_metadata.py tests/test_hosted_plugin_layout.py tests/test_runtime_installers.py tests/test_manual_install_layout.py tests/test_extension_mirrors.py tests/test_extension_installer_injection.py tests/test_banana_install_layout.py tests/test_banana_key_masking.py tests/test_dataforseo_tool_names.py tests/test_consistency_check.py tests/test_portability.py tests/test_ai_crawler_claims.py -q`: 77 passed, 24 skipped.
- `python -m pytest tests/ -v`: exit 1; 3,773 passed, 68 skipped, 77 subtests passed, and 1 warning (warning detail unavailable), with 3 reproducible failures:
  - `tests/test_banana_cost_tracker.py::test_concurrent_logs_do_not_lose_entries`: 4 of 20 worker processes failed with Windows `msvcrt.locking` “Resource deadlock avoided” at line 84.
  - `tests/test_dataforseo_costs.py::test_concurrent_logs_do_not_lose_entries`: 2 of 20 worker processes failed with the same Windows `msvcrt.locking` error at line 71.
  - `tests/test_google_api_key_safety.py::test_mcp_docs_do_not_show_google_query_key_examples`: assertion at line 162 failed because `docs/MCP-INTEGRATION.md` does not contain `X-Goog-Api-Key`.

The three full-suite failures above were baseline findings at P1-QA-02 and were not ecommerce-task regressions. They were investigated and resolved in the P1-RED-01 continuation below; retain this section as the historical pre-fix record.

### Plugin package and runtime checks

- `python scripts/sync_codex_skill.py --check`: passed.
- `python -m unittest discover -s tests -p test_plugin_package.py -v`: 10 passed, 2 skipped.
- `python -m pytest tests/test_plugin_package.py -q`: 10 passed, 2 skipped, 77 subtests passed.
- `python scripts/build_plugin.py --output dist/codex-seo-plugin.zip`: passed. `python -m zipfile -t dist/codex-seo-plugin.zip` and `python -m zipfile -l dist/codex-seo-plugin.zip` passed; archive lists 77 files, is 53,056 bytes, SHA-256 `DF4745DEBAB6F6FA40A051C910525865626BFE4BA82CEE1157C37883C8B0F19E`.
- `./scripts/codex-seo setup`: exit 0.
- `./scripts/codex-seo doctor --json`: exit 0; `ready=true`, `browser_ready=true`, Python 3.12, plugin 2.6.2. Root repeated this doctor check in Git Bash with the bundled Python PATH and got the same result.
- `./scripts/codex-seo run render_page.py https://example.com --mode auto --json`: exit 0; HTTP 200, raw mode, without Chromium.
- `./scripts/codex-seo run render_page.py https://example.com --mode always --json`: exit 0; HTTP 200, rendered using Playwright Chromium with sandbox enabled and no errors.
- `./scripts/codex-seo run seo_updates.py --limit 1 --json`: exit 0; returned 1 of 66 matching updates and marked the result truncated. The newest update was last verified on 2026-11-10.

### Extension and desktop smoke checks

- In a disposable clone at the recorded base, `./extensions/shopify/install.sh` and `./extensions/shopify/uninstall.sh` passed, as did renamed-checkout relative-link resolution, repeat install, placeholder creation, and placeholder preservation on rerun. The placeholder SHA-256 was `80bb5b5407469adfd27975880155b7e7ee70fb6451b42751d77c2f31ab3f5477`.
- The PowerShell Shopify command `& '.\extensions\shopify\install.ps1'` initially could not locate Python. After adding `.venv-dev/Scripts` and Git Bash to PATH, the same install command passed. The subsequent uninstall was performed with Bash `./extensions/shopify/uninstall.sh` and passed; a PowerShell uninstall was not run.
- ChatGPT Desktop showed the plugin under Plugins > Installed and the documented prompt completed. The response produced an audit but explicitly disclaimed verified Codex SEO skill invocation or an automated suite. Plugin visibility and prompt completion were observed; actual plugin skill invocation remains PARTIAL/UNVERIFIED.
- Codex Desktop smoke passed in a fresh projectless local Codex task. The task read the installed `created-by-me-remote\codex-seo\0.1.0\skills\seo\SKILL.md` and technical/schema guides, then called `webSearch` and completed a response. This verifies discovery and use in that smoke task, not general behavior across other workspaces or sessions.

The QA execution itself changed no source or docs; this record was added afterward. At the time of the P1-QA-02 workstation record, the full suite had three unresolved failures. See P1-RED-01 below for their resolution and the later final suite result.

## Ecommerce continuation verification (2026-11-20, ECO-DEL-04)

This record supplements P1-QA-02 and the earlier Task 2 evidence. Work remained on `codex-native-support`, expected remote base `f321d58`; the branch was ahead by four commits. At the time of the ECO-DEL-04 run, the working tree modified `docs/PHASE1-VERIFICATION.md`, `scripts/ecommerce_page_check.py`, `scripts/runtime.py`, `skills/seo-ecommerce/SKILL.md`, `tests/test_ecommerce_page_check.py`, and `tests/test_runtime.py`. No commit, push, merge, or publication was performed.

### Checker and project verification

- `.venv-dev/Scripts/python.exe -m pytest tests/test_ecommerce_page_check.py -q`: 15 passed. Before final characterization, `.venv-dev/Scripts/python.exe -m pytest tests/test_ecommerce_page_check.py tests/test_runtime.py -q` passed 38 tests. Before the final assertion-only addition, `.venv-dev/Scripts/python.exe -m pytest tests/test_ecommerce_page_check.py tests/test_parse_html_extraction.py tests/test_schema_validator_redos.py tests/test_schema_validator_policy.py tests/test_schema_validator_detection.py tests/test_schema_validator_cli.py tests/test_schema_v2.py tests/test_schema_singleton_graph.py tests/test_schema_policy_lists.py tests/test_schema_malformed_offers.py tests/test_schema_graph_semantics.py tests/test_schema_expanded_types.py tests/test_runtime.py -q` passed 232 tests. The final current-tree combined command and result are recorded below in the post-documentation refresh.
- `.venv-dev/Scripts/python.exe -m pytest tests/ -v`: at that point, exit 1; 3,787 passed, 68 skipped, 77 subtests, 4 failures, and 1 warning. Three failures matched the recorded baseline: `test_banana_cost_tracker::test_concurrent_logs_do_not_lose_entries`, `test_dataforseo_costs::test_concurrent_logs_do_not_lose_entries`, and `test_google_api_key_safety::test_mcp_docs_do_not_show_google_query_key_examples`. The additional `test_banana_cost_tracker::test_concurrent_logs_keep_aggregates_correct` had passed once when rerun alone (1 passed in 8.67s), so it was not reproduced then and appeared timing-sensitive. The warning was Matplotlib tight-layout in `test_report_robustness::test_long_crux_and_history_labels_keep_charts_small`. These results were superseded by P1-RED-01 below.
- `.venv-dev/Scripts/python.exe scripts/check_codex_cleanup.py`: passed. `.venv-dev/Scripts/python.exe scripts/consistency_check.py --json`: 742 files, 0 errors/warnings (informational cross-skill links). `.venv-dev/Scripts/python.exe scripts/portability_check.py --json`: 40 skills, 0 errors/warnings. `.venv-dev/Scripts/python.exe scripts/sync_codex_skill.py --check`: passed (76 files).
- `.venv-dev/Scripts/python.exe -m pytest tests/test_plugin_package.py -q`: 10 passed, 2 skipped, 77 subtests. `.venv-dev/Scripts/python.exe scripts/build_plugin.py --output dist/codex-seo-plugin.zip`: passed; `.venv-dev/Scripts/python.exe -m zipfile -t dist/codex-seo-plugin.zip` and `.venv-dev/Scripts/python.exe -m zipfile -l dist/codex-seo-plugin.zip` passed. ZIP contains 77 files, is 53,661 bytes, SHA-256 `53f548038e5404de7a2ab7e8e4b75059a05d463a96e89c3d23a7abde62b0085b`.
- `git diff --check`: clean; Git emitted line-ending conversion warnings for modified Python files.

### Post-documentation verification refresh

Root reran focused and supporting checks on the final working tree after this record was added. This refresh does not replace the full-suite result above.

- `.venv-dev/Scripts/python.exe -m pytest tests/test_ecommerce_page_check.py tests/test_runtime.py -q`: 39 passed in 1.07s.
- `.venv-dev/Scripts/python.exe scripts/check_codex_cleanup.py`: passed. `.venv-dev/Scripts/python.exe scripts/consistency_check.py --json`: 742 files, 0 errors/warnings; informational cross-skill link messages only. `.venv-dev/Scripts/python.exe scripts/portability_check.py --json`: 40 skills, 0 errors/warnings. `.venv-dev/Scripts/python.exe scripts/sync_codex_skill.py --check`: passed (76 files).
- `.venv-dev/Scripts/python.exe -m pytest tests/test_plugin_package.py -q`: 10 passed, 2 skipped, 77 subtests. `.venv-dev/Scripts/python.exe scripts/build_plugin.py --output dist/codex-seo-plugin.zip`: passed (77 files). `.venv-dev/Scripts/python.exe -m zipfile -t dist/codex-seo-plugin.zip`: “Done testing”; `.venv-dev/Scripts/python.exe -m zipfile -l dist/codex-seo-plugin.zip`: 77-file listing. Archive size: 53,661 bytes; SHA-256: `53f548038e5404de7a2ab7e8e4b75059a05d463a96e89c3d23a7abde62b0085b`.
- `git diff --check`: clean; only Git line-ending conversion warnings were reported from status.
- ECO-QA-06 independent review was clean. A unique exact option-value-to-SKU association selects the Offer even when a custom label does not match a product name; the literal label mismatch remains visible. If the label names another Product, the selected variant and all Offer comparisons are ambiguous and schema is null. ECO-QA-DOC-02 was clean for the checkout-only command. Task 1 independent review was clean.

### Public G&R Finds sample (bounded read-only check, not a full audit)

Runtime doctor via `.venv-dev/Scripts/python.exe scripts/runtime.py doctor --json` reported `ready=true`, `browser_ready=true`, mode `manual`, Python 3.12. The following managed commands succeeded:

```powershell
.venv-dev/Scripts/python.exe scripts/runtime.py run fetch_page.py https://shop.grfinds.site/ --output C:/Users/zirc/AppData/Local/Temp/codex-seo-grfinds-home.html --json --max-text 2500 --timeout 30
.venv-dev/Scripts/python.exe scripts/runtime.py run fetch_page.py https://shop.grfinds.site/shop --output C:/Users/zirc/AppData/Local/Temp/codex-seo-grfinds-shop.html --json --max-text 1800 --timeout 30
.venv-dev/Scripts/python.exe scripts/runtime.py run sitemap_discovery.py https://shop.grfinds.site/ --expand --max-children 10 --sample 25 --json
.venv-dev/Scripts/python.exe scripts/runtime.py run render_page.py https://shop.grfinds.site/shop --mode always --json --output C:/Users/zirc/AppData/Local/Temp/codex-seo-grfinds-shop-rendered.html --max-text 2500
.venv-dev/Scripts/python.exe scripts/runtime.py run ecommerce_page_check.py C:/Users/zirc/AppData/Local/Temp/codex-seo-grfinds-shop-rendered.html
```

The homepage fetch returned HTTP 200 raw, 59,045 bytes, with headers exposed. `/shop` returned HTTP 200 raw, 56,805 bytes. Robots declared one valid `/sitemap.xml` urlset; all 12 sitemap URLs were returned, with no product URLs. Common sitemap index alternatives returned 404. The sitemap includes `/shop` and public policy paths; policy contents were not reviewed. Rendered `/shop` returned HTTP 200 using Playwright Chromium with sandbox enabled, no console errors, and no significant JavaScript gap. Visible text said “0 pieces to explore” and “The collection is being styled. New pieces will appear here as they are added.” The offline checker exited 0 and found no Product entity; product-specific facts were unavailable and it emitted `missing-product` for the collection page.

This sample does not test a live Product/Offer match: no product page was found. It does not confirm prelaunch or paused checkout; no checkout was attempted. Indexing, Search Console, and rankings were not measured. Historical G&R audit facts remain supplied context and were not re-verified, except the current empty shop and sitemap observations above. At the time of this sample, ChatGPT Desktop smoke remained PARTIAL/UNVERIFIED, and the Codex Desktop smoke covered only the already-installed private plugin. The later private plugin update and pending Desktop checks are recorded in P1-VERIFY-WSL-03 below.

### Task 3 decision and limits

No sampler will be added. Existing guarded `fetch_page.py` and `render_page.py`, `parse_html.py` link extraction, and `sitemap_discovery.py` support manually bounded same-origin selection; the checked site exposed no product URL for a sampler to compare. This is a local decision only, with no implementation. Runtime model and effort telemetry were not exposed and remain UNVERIFIED.

## Phase 1 full-suite repair (2026-11-20, P1-RED-01)

This continuation supersedes the historical red-suite results above. It ran in the existing `C:\dev\codex-seo` checkout on `codex-native-support` with `.venv-dev/Scripts/python.exe` (Python 3.12.14), preserving the pre-existing ecommerce edits. No commit, push, merge, release, publication, or live-site write was performed.

### Root causes and regressions

- The Windows branches in both cost ledgers used `msvcrt.LK_LOCK`, whose CRT retries contention only ten times with one-second intervals. Under 20 concurrent CLI subprocesses, waiting writers exceeded that bounded window and failed with `OSError: [Errno 36] Resource deadlock avoided`; a direct Banana reproduction reported 3 failed writers. The aggregate test consequently observed 17 rather than 20 images. Both ledgers now use `LK_NBLCK` and retry only the Windows contention errors `EACCES` and `EDEADLK`, preserving propagation of other lock errors and keeping the ledger fail-closed. POSIX `fcntl` code is unchanged.
- The Google API safety test intentionally requires docs to identify `X-Goog-Api-Key` and reject query-string examples. The MCP integration guide previously omitted the header name. It now explains header transport and warns against URLs, logs, and shared examples; the test's safety assertions were not weakened.
- RED evidence before implementation: `.venv-dev/Scripts/python.exe -m pytest tests/test_banana_cost_tracker.py::test_concurrent_logs_keep_aggregates_correct -q` failed after 4 child processes raised the Windows lock error. `.venv-dev/Scripts/python.exe -m pytest tests/test_google_api_key_safety.py::test_mcp_docs_do_not_show_google_query_key_examples -q` failed because the header was absent. A direct 20-process Banana run failed 3 children at `msvcrt.locking` in `_lock`.

### Final verification

- `.venv-dev/Scripts/python.exe -m pytest tests/test_banana_cost_tracker.py tests/test_dataforseo_costs.py tests/test_google_api_key_safety.py -q`: exit 0, 24 passed in 8.39s.
- Five sequential runs of `.venv-dev/Scripts/python.exe -m pytest tests/test_banana_cost_tracker.py::test_concurrent_logs_keep_aggregates_correct -q`: all five passed (each run starts 20 simultaneous CLI writers; durations 0.78–0.81s).
- POSIX/WSL focused concurrency run: `wsl.exe --exec bash -lc 'cd /mnt/c/dev/codex-seo && PYTHONPATH=/mnt/c/Users/zirc/AppData/Local/Temp/codex-seo-p1-posix-pytest-20261120 python3 -m pytest tests/test_banana_cost_tracker.py tests/test_dataforseo_costs.py -q'`: 17 passed in 5.20s under Ubuntu/WSL Python 3.12.3 using POSIX `fcntl`. No system packages were installed.
- `.venv-dev/Scripts/python.exe -m pytest tests/ -v`: exit 0; 3,791 passed, 68 skipped, 77 subtests passed in 198.05s, with one warning. The warning is `UserWarning` from `scripts/google_report.py:317` during `tests/test_report_robustness.py::test_long_crux_and_history_labels_keep_charts_small` because Matplotlib cannot fit all axis decorations in the margins. No tests failed.
- `.venv-dev/Scripts/python.exe scripts/check_codex_cleanup.py`: passed (`Codex product cleanup passed. Upstream notices and crawler labels are allowed.`).
- `.venv-dev/Scripts/python.exe scripts/portability_check.py`: passed; 40 skills checked, 0 errors, 0 warnings, 0 info.
- `.venv-dev/Scripts/python.exe scripts/sync_codex_skill.py --check`: passed; checkout skill matches portable source (76 files).
- `git diff --check`: exit 0. Git emitted line-ending conversion advisories for the pre-existing modified `scripts/ecommerce_page_check.py` and `tests/test_ecommerce_page_check.py`; no whitespace errors.

The Windows subprocess concurrency regressions were exercised directly on Windows. The related ledger tests also passed under WSL/POSIX, exercising the unchanged `fcntl` path; Linux outside WSL and macOS were not tested. The first independent review found only a missing POSIX verification run. After the WSL evidence was added, the reviewer returned CLEAN for spec compliance and code quality, with no findings. The full-suite test result applies to this checkout state and does not validate external integrations or live-site behavior.

At P1-RED-01 completion, ChatGPT skill invocation remained PARTIAL/UNVERIFIED, and the Codex Desktop smoke had tested only the already-installed private plugin, not the local unpublished changes. The private plugin was subsequently updated to 0.1.1; Desktop verification for that release remains pending as recorded below. Runtime model and effort telemetry were not exposed and remain UNVERIFIED.

## Phase 1 WSL and private plugin continuation (2026-11-20, P1-VERIFY-WSL-03)

This record supersedes earlier statements that no private plugin update had occurred and that the source remained unpublished to plugin hosts. The repository work remains local on `codex-native-support`; no GitHub push or repository publication occurred. Phase 2 is on hold until the manual Desktop smoke checks for private plugin version 0.1.1 are complete.

### Package and private plugin update

- `.venv-dev/Scripts/python.exe scripts/build_plugin.py --output dist/codex-seo-plugin.zip`: passed; the local ZIP contains 77 files, is 53,661 bytes, and has SHA-256 `53f548038e5404de7a2ab7e8e4b75059a05d463a96e89c3d23a7abde62b0085b`. `.venv-dev/Scripts/python.exe -m zipfile -t dist/codex-seo-plugin.zip`: passed.
- `.venv-dev/Scripts/python.exe -m pytest tests/test_plugin_package.py -q`: 10 passed, 2 skipped, and 77 subtests. The subtests cover six invalid reference-definition forms, two missing or escaping link cases, and 69 bundled reference Markdown files.
- On the Windows run, the two skipped plugin-package tests require symlink behavior unavailable in that environment. The equivalent focused run in WSL/POSIX passed 12 tests and 77 subtests in 1.20s, including those symlink tests.
- With the user's authorization, Plugin Creator updated the existing USER-scoped PRIVATE plugin `codex-seo` from version 0.1.0 to 0.1.1. Plugin ID: `plugins_6aff1ef6b5b88191a1c5a3f68299b014`; release ID: `pluginrel_6b00466b2c048191ad3b46720c517492`; [private plugin link](https://chatgpt.com/plugins/plugins_6aff1ef6b5b88191a1c5a3f68299b014).
- The remote private plugin contains 78 files: the 77 local archive files plus host-managed `.codex-plugin/plugin.json`. The updated `skills/seo/references/guides/seo-ecommerce.md` is present. This was a private plugin update; no GitHub push or repository publication occurred.
- Desktop smoke has not been rerun for version 0.1.1. The observed Codex cache still contains version 0.1.0. ChatGPT Desktop invocation remains PARTIAL/UNVERIFIED, and neither ChatGPT Desktop nor Codex Desktop has been verified against 0.1.1. Do not treat either previous Desktop smoke as a pass for the updated release.

### Windows and WSL test results

- A later Windows full-suite run, `.venv-dev/Scripts/python.exe -m pytest tests/ -q -rs`, passed: 3,791 passed, 68 skipped, 77 subtests, and one Matplotlib tight-layout warning in 178.39s. The captured output did not preserve the exact per-test Windows skip breakdown; these are platform/environment skips, so no more specific breakdown is claimed here.
- The 77 subtests are from `tests/test_plugin_package.py`, as described above.
- An initial WSL full-suite attempt directly from `/mnt/c/dev/codex-seo` was non-authoritative and failed with 30 failures, 3,824 passed, and 5 skipped. The environment exposed CRLF/DrvFs limitations (`scripts/codex-seo` rejected `set: pipefail` and the case-sensitivity probe was limited) and missing Chromium libraries (`libnspr4.so`, `libnss3.so`, `libnssutil3.so`, and `libasound.so.2`). This was an environment-specific attempt, not treated as a code regression or as the WSL result.
- The authoritative WSL run used a Linux-native disposable copy made from the current local HEAD plus `git diff --binary`, under `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/source` on the WSL ext4 filesystem. Its venv, pip cache, Playwright browser, and downloaded/extracted system libraries are under the same disposable root. The exact test command was run from `$root/source`:

```bash
env -u CODEX_SEO_NETWORK_TESTS \
  LD_LIBRARY_PATH="$root/system-libs/usr/lib/x86_64-linux-gnu" \
  PLAYWRIGHT_BROWSERS_PATH="$root/playwright" \
  PYTHONDONTWRITEBYTECODE=1 \
  "$root/venv/bin/python" -m pytest tests/ -q -rs
```

  Here `$root` was `/home/zirc/.cache/codex-seo-phase1-wsl-20261120`. The command exited 0: 3,854 passed, 5 skipped, 77 subtests, 2 warnings, in 104.18s. The skips were: one case-sensitive-filesystem probe; three live GitHub API tests gated by unset `CODEX_SEO_NETWORK_TESTS`; and one Node.js-dependent test skipped because Node.js was unavailable. The warnings were a WeasyPrint HarfBuzz-Subset deprecation and the existing Matplotlib tight-layout warning.
- WSL supporting checks passed: `scripts/check_codex_cleanup.py`; `scripts/consistency_check.py --json` (742 files, 0 errors/warnings); `scripts/portability_check.py --json` (40 skills, 0 errors/warnings); and `scripts/sync_codex_skill.py --check` (76 files). The focused POSIX ledger tests had also passed earlier: 17 passed under WSL/POSIX `fcntl`.

### Test environment and Phase 1 gate

- No apt/system packages were installed. The WSL full-suite run used downloaded/extracted libraries and browsers inside its disposable root.
- Temporary Windows paths retained for later removal: `C:\Users\zirc\AppData\Local\Temp\codex-seo-p1-virtualenv-bootstrap-20261120`; `C:\Users\zirc\AppData\Local\Temp\codex-seo-p1-posix-pytest-20261120`; and `C:\Users\zirc\AppData\Local\Temp\codex-seo-p1-wsl-working.diff`. The durable disposable WSL environment is `/home/zirc/.cache/codex-seo-phase1-wsl-20261120`.
- An earlier unsuccessful WSL venv attempt left the untracked `.venv-posix/` directory in the checkout. It was not removed or modified during this continuation.
- The manually requested ChatGPT Desktop and Codex Desktop smoke checks for version 0.1.1 remain outstanding; the user will run both checks. Phase 2 stays on hold until their results are recorded. No local source or test code changed in this continuation.

## Desktop smoke follow-up for private plugin 0.1.1 (2026-11-20, P1-DESKTOP-02)

This later record supersedes the outstanding Desktop-smoke status above. The local repository remains on `codex-native-support`; this verification added no code or site changes, and no GitHub push, merge, or publication occurred. Phase 2 remains on hold because the ChatGPT Work result is not yet available.

- **Codex Desktop: PASS for plugin discovery/invocation and the requested read-only G&R audit.** The session loaded the installed `created-by-me-remote\codex-seo\0.1.1\skills\seo\SKILL.md` and the bundled audit, ecommerce, sitemap, and schema guides. After its initial prompt omitted a URL, the user supplied `https://shop.grfinds.site/`. The completed report covered the G&R Finds shop and linked its public evidence.
- The Codex audit observed the rendered `/shop` state as “0 pieces to explore” and “The collection is being styled”; it reported that the public policies said checkout was paused and kept the empty-catalog finding conditional on prelaunch. It reported 12 sitemap URLs, all returning HTTP 200 in its URL checks, with no product URLs. The report did not infer indexation or rankings from the sitemap and left Search Console, analytics, Merchant Center, mobile, and field/lab Core Web Vitals unavailable.
- A follow-up in the same Codex session clarified HTTP status and `Content-Type`/`Content-Length` were inspected for `robots.txt`, the homepage, `/shop`, and the sitemap. Full response headers were not inspected; `X-Robots-Tag`, cache, and security headers remain unavailable from this audit. Indexing remains unavailable without Search Console URL Inspection or an export; sitemap membership or omission does not establish indexation.
- **ChatGPT Work: NOT PASSED; pending/unverified for G&R Finds.** The initial “audit this website” prompt omitted a URL, and the response audited `domain.doofs.tech` by inferring it from prior conversation context. That is the wrong target and does not satisfy this smoke check. An authorized follow-up explicitly named `https://shop.grfinds.site/` and requested a read-only, evidence-labeled audit. The connected history shows that prompt as the latest completed turn but exposes no assistant response; no pass is recorded until a response for the correct target is available and reviewed.
- No checkout action, site write, paid provider request, indexing submission, GitHub operation, or plugin publication occurred in these checks. The previous line saying the user would run both checks is historical; Codex Desktop is now verified for 0.1.1, while ChatGPT Work remains the only outstanding desktop gate. Phase 2 remains paused.

## Desktop smoke completion for private plugin 0.1.1 (2026-11-20, P1-DESKTOP-03)

This continuation supersedes P1-DESKTOP-02's pending ChatGPT Work result. Both user-facing Desktop smoke workflows are now complete for the updated private plugin. The Phase 1 verification gate is satisfied, with the platform skips and unavailable evidence recorded above. Phase 2 may proceed as a read-only G&R Finds review of public product discovery and policy pages; no store write or GitHub publication is implied or authorized by this status.

- **ChatGPT Work: PASS for user-facing invocation and the corrected target.** In the `SEO Audit Plan` chat, the corrected turn explicitly audited `https://shop.grfinds.site/` and returned a read-only G&R Finds report. It covered the homepage, `/shop`, `robots.txt`, `sitemap.xml`, the policy index, and linked policies; a rendered browser was available. It kept the empty catalog conditional on prelaunch, stated that the sitemap does not establish indexing or rankings, and labeled raw source, response headers/status, indexing/rankings, analytics, and performance as unavailable for that run. Dedicated crawler and Search Console data were unavailable. The plugin-directory screenshot showed version 0.1.1, but the ChatGPT history does not expose an exact skill-file load or runtime-version signal; that internal telemetry remains **UNVERIFIED**.
- The ChatGPT audit observed all 12 sitemap URLs with `lastmod` value `2026-11-20T14:14:05.677Z`. The earlier Codex Desktop audit observed `2026-11-20T00:12:35.599Z`. These are time-specific snapshots and must not be treated as a stable sitemap timestamp.
- **Codex Desktop: PASS for plugin discovery/invocation and the requested read-only G&R audit.** As recorded in P1-DESKTOP-02, the session loaded the cached 0.1.1 skill and clarified which response headers were inspected and which remained unavailable.
- Both Desktop results are limited to their reported public-page scope. No checkout action, store write, indexing submission, paid-provider call, GitHub operation, plugin release, or public publication occurred. Existing environment-dependent test skips and other unavailable measurements remain as documented; this does not claim universal behavior across every host or workspace.

## Phase 1 limits follow-up (2026-11-21, P1-RESOLVE-LIMITS)

This continuation reran the final suite after fixing the Phase 1 documentation house-style failure and the confirmed long-label chart readability issue. Tests ran in a Linux-native disposable source copy at `/home/zirc/.cache/codex-seo-p1-limits-20261121/source`. The copy was made from current `HEAD` plus the tracked working-tree diff. To run POSIX launcher tests correctly, only the 22 extension shell wrappers and `scripts/codex-seo` were normalized to LF in that disposable copy; the Windows checkout and all original uncommitted files were left unchanged. The updated `docs/PHASE1-VERIFICATION.md` was copied into the disposable source before testing.

### Fresh full suite

With `root=/home/zirc/.cache/codex-seo-p1-limits-20261121` and `old=/home/zirc/.cache/codex-seo-phase1-wsl-20261120`, the exact command from `$root/source` was:

```bash
env -u CODEX_SEO_NETWORK_TESTS \
  LD_LIBRARY_PATH="$old/system-libs/usr/lib/x86_64-linux-gnu" \
  PLAYWRIGHT_BROWSERS_PATH="$old/playwright" \
  PATH="$root/node/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
  "$old/venv/bin/python" -m pytest tests/ -q -rs
```

Result: exit 0, **3,856 passed, 4 skipped, 77 subtests passed, 1 warning**, in 104.36s. Full output is retained at `/home/zirc/.cache/codex-seo-p1-limits-20261121/full-suite-post-chart.log`.

### Skips and environment limits

- `tests/test_unlighthouse_run.py::test_node_preflight_redirect_cannot_reach_internal_server` passed with isolated Node v26.13.1 at `$root/node/bin`; this removes the earlier Node-missing skip. No system package was installed.
- `tests/test_profile_paths.py::test_home_directory_in_different_case_is_rejected` remains skipped on WSL ext4 because that filesystem is case-sensitive. Its focused Windows counterpart passed, 1 test, using `C:\Users\zirc\AppData\Local\Temp\codex-seo-p1-limits-win-20261121\Scripts\python.exe`.
- The three `tests/test_sync_flow.py` live GitHub API tests remain gated in the full run because `CODEX_SEO_NETWORK_TESTS` was unset. A bounded unauthenticated opt-in attempt ran the live checks without credentials; one passed, and two were skipped after GitHub returned HTTP 403 rate limits. Do not mark those three as passed in the full run or repeat calls without a reason to expect the public rate limit to have cleared.
- The initial Linux snapshot run had 28 failures because its POSIX wrappers retained CRLF from the Windows working copy, plus the documentation em-dash check. In the disposable copy, LF normalization made the affected shell/launcher subset pass, 43 tests; changing the Desktop status punctuation to colons made `tests/test_no_em_dash.py` pass, 4 tests. No source wrapper or unrelated document was changed to work around the copy issue.
- WSL's system Python lacks `python3-venv`/ensurepip. The run reused the existing isolated WSL virtual environment and downloaded runtime assets; no apt/system packages were installed.

### Warning review and resolution

- The Matplotlib `tight_layout` warning from the long CrUX distribution label was a real readability issue: its 60-character unbroken y-axis label consumed most of the 3,178-pixel chart width. The label now wraps at 24 characters after truncation. A test-first regression check confirmed the old warning before the change; the new and existing long-label tests pass, and the chart now measures 1,622 x 474 pixels with the label visible over three lines. The warning no longer occurs for this fixture. Independent review returned clean for spec compliance and code quality.
- The remaining warning is a third-party WeasyPrint deprecation at `weasyprint/text/ffi.py:528`: HarfBuzz-Subset will be required by future WeasyPrint versions. It is not a project test failure; no warning suppression or dependency change was made.
- `git diff --check` exited 0. It printed only the existing LF-to-CRLF advisories for `scripts/ecommerce_page_check.py` and `tests/test_ecommerce_page_check.py`.

### Phase 1 disposition

All runnable Phase 1 checks pass in the isolated WSL run, with the four skips above explicitly retained. The case-sensitivity behavior was also verified on Windows. The public GitHub tests remain unverified under the current unauthenticated rate limit. ChatGPT Work and Codex Desktop user-facing smoke checks pass for private plugin 0.1.1; ChatGPT's exact internal skill-load telemetry remains **UNVERIFIED** because the host does not expose that signal. No commit, push, release, live-site change, or publication occurred.

Disposable paths retained for removal only if later requested: `/home/zirc/.cache/codex-seo-p1-limits-20261121`, `C:\Users\zirc\AppData\Local\Temp\codex-seo-p1-limits-win-20261121`, and the earlier `/home/zirc/.cache/codex-seo-phase1-wsl-20261120` environment. No cleanup was performed.

## Local 0.1.2 release-candidate verification (2026-11-21)

This section records verification of the local 0.1.2 package candidate and related checkout changes. Version 0.1.2 is a local candidate only. It has not been installed or smoke-tested in ChatGPT Desktop or Codex Desktop, uploaded, submitted, released, or published. The historical private-plugin 0.1.1 desktop results above remain scoped to 0.1.1 and are not evidence for 0.1.2.

### Candidate suite and disposable ext4 snapshot

- The full final-candidate suite ran in a disposable WSL ext4 snapshot before the later privacy-recipient wording and its test-only delta: **3,866 passed, 4 skipped, 79 subtests, and one third-party WeasyPrint deprecation warning**, in 102.95 seconds.
- The initial Windows-to-WSL copy had 22 POSIX-wrapper failures caused by CRLF line endings. In the disposable ext4 snapshot only, normalizing those 22 wrappers to LF made the focused wrapper suite pass, 34/34, and the full suite pass. No source wrapper was changed, and the unnormalized copy did not pass.
- The four full-suite skips were the three live GitHub API tests gated by the unset network-test flag and one case-sensitivity test. The warning was the third-party WeasyPrint deprecation; it was not a project test failure.

### Final privacy and package delta

- The later privacy wording and package-test delta was checked separately in a fresh ext4 snapshot at `/home/zirc/.cache/codex-seo-final-candidate-privacy-20261121/source`. The focused plugin pytest run passed, **17 tests and 79 subtests**; the plugin unittest run passed, **17/17**.
- The package build passed with 79 files. The ZIP integrity check passed and the archive contains both PNG assets. The archive is 2,070,341 bytes with SHA-256 `755dfdc49f2b52531827f588e948b2c8e13eddc4b17f631c1aadc70eac634b4f`. Skill synchronization passed with 76 files. The build log is `/home/zirc/.cache/codex-seo-final-candidate-privacy-20261121/logs/package-privacy-build-final.log`.
- This package snapshot verifies the local candidate archive and the privacy addendum/test delta. It does not represent an upload, submission, desktop installation, or publication.

### Isolated runtime and lifecycle checks

- The isolated checkout runtime setup reported ready. Doctor reported `ready=true`, `browser_ready=true`, and Python 3.12. The SEO updates command returned one result out of 66 and identified the output as truncated.
- Raw and Playwright Chromium checks against `https://example.com` both returned HTTP 200. The Playwright result reported `sandbox=true`, no console errors, and 1.34 seconds.
- Shopify lifecycle checks passed in a separate disposable copy: the guide path was present; install survived a rename-after-install check; uninstall passed; the audit environment placeholder had mode 600; and the rerun marker was verified. These checks used a placeholder, not a real credential.

### Repository and release state

- These results are scoped to the stated disposable snapshots and commands. They do not establish live-site ranking, indexing, search visibility, or provider outcomes.
- No commit, push, pull request, release, upload, submission, or publication was performed for the 0.1.2 candidate. No 0.1.2 desktop smoke was run.

## Gate 2 public product-fact assessment (2026-11-21)

**Status: INCOMPLETE.** This was a read-only assessment using the managed WSL Python environment at `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python`. Raw HTTP pages were checked and saved locally. The checker was run against the saved HTML from the final-candidate snapshot; this did not select options or interact with Add to cart, cart, or checkout.

### Product pages with bounded checker results

- [Arduino UNO R4 WiFi](https://store.arduino.cc/products/uno-r4-wifi) returned raw HTTP 200. Its saved source is `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/arduino-uno-r4-wifi.html`. The visible H1 `Arduino® UNO R4 WiFi` matched the Product JSON-LD identity. The associated structured Offer reports 22.88 EUR and InStock. The checker reported visible amount, currency, availability, and selected variant as **unavailable**; those comparisons remain unavailable with schema values 22.88, EUR, and InStock. The raw page contains multiple euro amounts and duplicates, including old and current pricing, so this source does not support a safe one-to-one visible Offer comparison.
- [Atlas Fitness Tank](https://www.scrapingcourse.com/ecommerce/product/atlas-fitness-tank/) returned HTTP 200. The checker reported identity **match** (`Atlas Fitness Tank`); visible amount, currency, availability, and selected variant were **unavailable**. The Product Offer contains $18.00 USD and OutOfStock. The category links to this product, but the source did not expose safe visible price/availability evidence associated with that Offer, so no conflict or match is inferred for those fields.
- The `abominable-hoodie` candidate showed a visible $69 amount, but the page has ProductGroup/variant context and no option was selected. Its amount was not used as a confirmed Offer comparison.

### Other candidate and access limits

IKEA's checked product had an identity mismatch; the Tricentis product had no JSON-LD Product; the OpenCart demo had no Product schema; and checked B&H, REI, and Sweetwater pages returned HTTP 403. The checked WooCommerce pages supported identity only, with price unavailable. A Hydrogen page had multiple Offers and ambiguous variant association. A Vercel-rendered page showed a visible price while its raw template hid the corresponding facts, so it did not provide a comparable raw-source result. These candidates do not close the product-fact verification gap.

No option selection, Add to cart, cart, or checkout interaction was performed. Invocation of candidate plugin version 0.1.2 in ChatGPT Desktop and Codex Desktop remains **UNVERIFIED**. Gate 2 remains incomplete until the ambiguous or unavailable visible facts are verified with a safely associated variant/Offer and the 0.1.2 desktop invocation is checked.

### Patagonia product-page observation (2026-11-21)

An existing Codex Desktop thread was invoked for a read-only Patagonia product-page check. The visible browser showed a Women's Better Sweater Fleece Jacket, style 25543, priced at $169, with Black initially selected and colors and sizes XXS–XXL. The page indicated a size selection would be required before Add to Bag could be enabled. The category page exposed a Better Sweater Jacket result. Direct HTTP requests for the product source and sitemap returned HTTP 200 maintenance HTML. JSON-LD/schema comparison, currency code, availability, sitemap membership, indexing/rankings, analytics, and performance therefore remain unavailable. No cart or checkout interaction occurred. The installed release at the time was 0.1.1; exact per-turn skill/version loading remains **UNVERIFIED**. This page view is not a checker match or evidence for candidate 0.1.2. Gate 2 remains **INCOMPLETE**, and candidate 0.1.2 desktop smoke remains **UNVERIFIED**.

### BigCommerce demo product check (2026-11-21)

The BigCommerce demo homepage at <https://apacdemostore.mybigcommerce.com/> linked to [Canvas Laundry Cart](https://apacdemostore.mybigcommerce.com/canvas-laundry-cart/). In the isolated WSL environment, `fetch_page.py` saved the raw product source to `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart.html` and exited 0 with raw HTTP 200. `ecommerce_page_check.py` exited 0 against that file. `render_page.py` with `--mode always` saved Playwright Chromium output to `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart-rendered.html`, exited 0 with HTTP 200, and reported 4,375 ms. The checker also exited 0 against the rendered HTML.

The recorded command lines were:

```powershell
wsl.exe -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python /mnt/c/dev/worktrees/codex-seo-ecommerce-fixes/codex-seo/scripts/fetch_page.py https://apacdemostore.mybigcommerce.com/canvas-laundry-cart/ --output /home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart.html
wsl.exe -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python /mnt/c/dev/worktrees/codex-seo-ecommerce-fixes/codex-seo/scripts/ecommerce_page_check.py /home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart.html
wsl.exe -- env LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/playwright PYTHONDONTWRITEBYTECODE=1 /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python /mnt/c/dev/worktrees/codex-seo-ecommerce-fixes/codex-seo/scripts/render_page.py https://apacdemostore.mybigcommerce.com/canvas-laundry-cart/ --mode always --output /home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart-rendered.html
wsl.exe -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python /mnt/c/dev/worktrees/codex-seo-ecommerce-fixes/codex-seo/scripts/ecommerce_page_check.py /home/zirc/.cache/codex-seo-phase1-wsl-20261120/ecommerce-gate2/bigcommerce-canvas-laundry-cart-rendered.html
```

Both checker runs parsed one Product/Offer and matched the visible identity `Canvas Laundry Cart`. The schema Offer reports price 200, currency AUD, and InStock; visible amount, currency, availability, and selected variant were **unavailable** because the page exposed current and former prices, only a currency symbol rather than a code, and a blank stock field, with no safely associated visible Offer evidence. Schema validation was `ok` with three medium and one informational finding. This is partial identity and Product/Offer parsing evidence, not verification of all Offer facts. No Add to cart or checkout interaction occurred. Response-header details, indexing/rankings, analytics, and performance remain unavailable; no conclusion is inferred from web extraction. Gate 2 remains **INCOMPLETE** and candidate 0.1.2 desktop smoke remains **UNVERIFIED**.

## Release verification continuation (2026-11-21)

This continuation records local release-candidate checks and desktop evidence taken before the source-branch push recorded below. At that time, the checkout was on `codex-native-support`, four commits ahead of `origin/codex-native-support`. Existing edits and untracked files were preserved. The repository was still in the Claude-SEO fork network; its public plugin-directory submission had not been made. Plugin version 0.1.2 was a USER-scoped PRIVATE plugin release, not a public directory release. No purchase or checkout interaction, live-site write, merge, fork detachment, or publication occurred as part of those checks.

### Current automated verification

- Fresh isolated WSL/ext4 full suite: exit 0, **3,866 passed, 4 skipped, 79 subtests passed**, one WeasyPrint HarfBuzz-Subset deprecation warning, in **103.28s**. Node v26.13.1 was available in the isolated environment.
- The four full-suite skips were one case-sensitive profile-path test (the WSL ext4 filesystem is case-sensitive) and three network-gated GitHub API tests. In a separate authenticated GitHub dry-run, one test passed and two were skipped after HTTP 403 rate limiting; the two rate-limited tests are not counted as passes.
- Windows focused run: **107 passed, 4 skipped, 79 subtests passed**.
- Supporting checks passed: cleanup; portability for 40 skills; skill mirror check for 76 files; consistency check for 742 files with no errors or warnings; `git diff --check` clean.
- Plugin archive build and ZIP integrity check passed. The archive contains 79 files; SHA-256 is `755dfdc49f2b52531827f588e948b2c8e13eddc4b17f631c1aadc70eac634b4f`.

### Private plugin and desktop observations

- The existing private plugin update to version 0.1.2 succeeded. Release ID: `pluginrel_6b0166ba4fc88191ab71acbcf0aecc99`. It remains USER-scoped and PRIVATE. It has not been submitted to the public plugin directory.
- **ChatGPT Work, `SEO Audit Plan`:** the BigCommerce smoke response reported observing product identity and price, currency ambiguous, and availability and variant unavailable. It said raw source and JSON-LD comparison were unavailable. The response did not expose a plugin version. It discovered and used available SEO guidance/checklist content but exposed no separate callable plugin audit tool. Exact 0.1.2 runtime identity remains **UNVERIFIED**; this is not a confirmed 0.1.2 plugin invocation.
- **Codex Desktop:** fresh thread `01a1fd7a-f185-7761-9582-730f6913ace9` loaded the cached skill at `created-by-me-remote\codex-seo\0.1.1`; the ecommerce guide was missing from that cache. The session reported matching identity, price, AUD currency, and availability based on extracted/raw data. Its browser was unavailable. This exercised cached 0.1.1, not 0.1.2, and is not a pass for the 0.1.2 candidate.

### Release and ecommerce gate status

Gate 2 remains **INCOMPLETE** because a safely associated, full visible Product/Offer fact comparison has not been established. The direct BigCommerce checker run matched identity and parsed the Offer, while amount, currency, availability, and selected variant remained unavailable; the Desktop reports do not establish those missing facts. No checkout interaction or site write occurred. The local source tree remains on `codex-native-support`; the 0.1.2 desktop invocation remains **UNVERIFIED**, the repository remains attached to the fork network, and public plugin-directory submission and merge to `main` have not occurred.

## Final documented pytest recheck (2026-11-21)

QA reran the documented pytest commands against a disposable WSL/ext4 snapshot at `/home/zirc/.cache/codex-seo-final-qa-20261121`. The snapshot's Git status was clean. The previous full-suite run recorded above (3,866 passed in 103.28 seconds) remains historical; this separate recheck completed in 105.53 seconds.

The environment was Python 3.12.3 at `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python` and Node v26.13.1 at `/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin`. The test process used `LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu`, `PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/playwright`, and `PYTHONDONTWRITEBYTECODE=1`; `CODEX_SEO_NETWORK_TESTS` was unset. These environment values are recorded separately; no additional shell command is inferred here.

### Focused and full pytest commands

From the repository root of the disposable snapshot, the documented focused groups and full suite returned:

```bash
python -m pytest tests/test_codex_agent_configs.py tests/test_agent_mcp_permissions.py tests/test_sync_flow.py tests/test_shopify_crawl.py -q
# 71 passed, 3 skipped, 0.32s

python -m pytest tests/test_manifest_consistency.py tests/test_pyproject_metadata.py tests/test_hosted_plugin_layout.py tests/test_runtime_installers.py tests/test_manual_install_layout.py tests/test_extension_mirrors.py tests/test_extension_installer_injection.py tests/test_banana_install_layout.py tests/test_banana_key_masking.py tests/test_dataforseo_tool_names.py tests/test_consistency_check.py tests/test_portability.py tests/test_ai_crawler_claims.py -q
# 101 passed, 1.19s

python -m pytest tests/ -v
# exit 0; 3,866 passed, 4 skipped, 79 subtests; one WeasyPrint
# HarfBuzz-Subset deprecation warning; 105.53s

python -m pytest tests/test_plugin_package.py -q
# 17 passed, 79 subtests, 1.67s
```

The four full-suite skips were the case-sensitive profile-path test and three network-gated GitHub API tests. In a separate authenticated GitHub dry-run, one test passed and two were skipped after HTTP 403 rate limiting. The full-suite result does not count those gated checks as passes. The full output for this exact recheck was captured by QA but no log file was retained.

The Windows focused run was reported as 107 passed, 4 skipped, and 79 subtests. Its exact command was not retained, so this entry records the outcome without reconstructing an invocation.

### Package and supporting checks

On the same candidate, the package archive contained 79 files and passed ZIP integrity validation; its SHA-256 was `755dfdc49f2b52531827f588e948b2c8e13eddc4b17f631c1aadc70eac634b4f`. Cleanup passed; portability passed for 40 skills; the skill mirror check passed for 76 files; consistency reported 742 files with no errors or warnings; and `git diff --check` was clean. A current source-checkout documentation test also passed: `wsl.exe -d Ubuntu-24.04 -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python -m pytest /mnt/c/dev/codex-seo/tests/test_no_em_dash.py -q` returned 4 passed.

## Source branch push and repository access update (2026-11-21)

After the recorded QA checks, commit `d354bb8c46f1a43a4fcddcb809aadcc2a333c730` (`Prepare SEO plugin verification updates`) was created and pushed normally to `origin/codex-native-support`. The remote branch now points to that commit, and the local branch is even with its upstream. The earlier statement that the branch was four commits ahead describes the pre-push snapshot only. The untracked `.venv-posix/` directory remains preserved and was not included in the commit.

No GitHub Actions runs or commit status checks were visible for the pushed branch at the time of this update. The repository remains public and attached to the `AgriciDaniel/claude-seo` fork network. `gh api repos/helx0071/codex-seo` reported `permissions.admin: false` for the authenticated account, so detaching the fork is blocked by the current credential. No pull request, merge, detach, or public plugin-directory submission has occurred. GitHub documents that leaving the fork network is permanent and requires repository admin access; an account with repository administration must perform that step.

The WSL test results above apply to the source snapshot tested before the push. The pushed commit contains that tested source and the related release documentation. The Codex Desktop cache was still on private plugin version 0.1.1, ChatGPT Work did not expose the invoked version, and the full visible Product/Offer fact comparison remains incomplete. These checks therefore do not establish a confirmed 0.1.2 invocation in both desktop hosts or complete Gate 2. No additional product-page, checkout, or indexing claim is made here.

## Independent repository creation (2026-11-21)

At the user's direction, a new public repository, `https://github.com/doofx0071/codex-seo`, was created under the connected GitHub account. The repository was empty when created; publishing the source tree to its `main` branch remains pending. The earlier public `helx0071/codex-seo` repository remains attached to the Claude-SEO fork network and has not been deleted or modified by this move. This is a source repository move, not a public plugin-directory release. The user chose to keep the existing version 0.1.2 plugin private; no public plugin listing was uploaded or submitted.

## ECOM-CHECK-16 visible semantic marker regression (2026-11-21)

The isolated worktree `C:\dev\worktrees\ecommerce-visible-facts\codex-seo` was checked out at source base `9bf2cf9` on local branch `codex/ecommerce-visible-facts`. The checker now reads rendered text only from the explicit visible `data-test="product-price-display-price"` and `data-test="product-overview-availability"` markers. It filters hidden descendants, collapses identical price duplicates, reports conflicting facts as ambiguous, does not infer currency from `$`, and does not infer a selected variant. The regression does not use the saved LEGO HTML as a live-site pass; its raw response was a Cloudflare challenge, so Gate 2 remains **INCOMPLETE**.

TDD evidence from WSL Ubuntu 24.04 using `/home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python`:

- Marker regression RED command: `wsl.exe -d Ubuntu-24.04 -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python -m pytest /mnt/c/dev/worktrees/ecommerce-visible-facts/codex-seo/tests/test_ecommerce_page_check.py -q -k 'explicit_visible_data_test or hidden_semantic or conflicting_semantic or identical_responsive_semantic'` returned **3 failed, 1 passed, 20 deselected**, as expected before the implementation.
- Hidden-descendant RED command: `wsl.exe -d Ubuntu-24.04 -- /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python -m pytest /mnt/c/dev/worktrees/ecommerce-visible-facts/codex-seo/tests/test_ecommerce_page_check.py -q -k semantic_markers_ignore_hidden_descendant_text_but_keep_visible_siblings` returned **1 failed, 24 deselected**, as expected before filtering hidden descendant text.
- Focused ecommerce and parser tests in the disposable ext4 snapshot: `python -m pytest tests/test_ecommerce_page_check.py tests/test_parse_html_extraction.py tests/test_parse_html_stdin_url.py tests/test_parse_html_size_cap.py tests/test_parse_html_rel_case.py tests/test_parse_html_malformed_urls.py tests/test_parse_html_inline_spacing.py -q` returned **143 passed**.
- Snapshot provenance: the disposable ext4 source was copied from `C:\dev\worktrees\ecommerce-visible-facts\codex-seo`, containing base `9bf2cf9` plus the reviewed working diffs to `scripts/ecommerce_page_check.py` and `tests/test_ecommerce_page_check.py`. It did not include the separate repository-metadata working diffs in `C:\dev\codex-seo`; this result verifies the checker regression and is not integrated final QA for the repository-metadata changes.
- Full suite command: `python -m pytest tests/ -v` from `/home/zirc/.cache/codex-seo-ecom-doc18-20261121/source`, with `LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu`, `PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/playwright`, `PATH` prefixed by `/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin`, `PYTHONDONTWRITEBYTECODE=1`, and `CODEX_SEO_NETWORK_TESTS` unset, returned exit 0: **3,871 passed, 4 skipped, 79 subtests passed**, one WeasyPrint HarfBuzz-Subset deprecation warning, **102.34s**. The four skips were one case-sensitive filesystem check and three live GitHub API checks skipped because the API was unavailable or rate limited. Node v26.13.1 and the provisioned Playwright Chromium were available; dependent browser and Node checks ran rather than being skipped.
- Documented focused pytest groups in the same isolated environment: first group **71 passed, 3 skipped**; second group **101 passed**. The 3 skips are the live GitHub API checks above. The initial tar copy preserved Windows CRLF in shell wrappers and caused shell-only failures; LF normalization was applied only inside the disposable ext4 snapshot, after which the second group passed. No repository shell files were changed for this environment correction.
- Focused ecommerce/parser command: `python -m pytest tests/test_ecommerce_page_check.py tests/test_parse_html_extraction.py tests/test_parse_html_stdin_url.py tests/test_parse_html_size_cap.py tests/test_parse_html_rel_case.py tests/test_parse_html_malformed_urls.py tests/test_parse_html_inline_spacing.py -q` returned **143 passed**. On a fresh snapshot of the current root documentation state, `python -m pytest tests/test_plugin_package.py tests/test_no_em_dash.py -q` returned **21 passed, 79 subtests passed**. `git diff --check` passed. An independent reviewer returned **PASS** for specification compliance and code quality with no remaining findings.

The previous desktop observations remain scoped to the older private version 0.1.1: Codex Desktop loaded cached 0.1.1, and ChatGPT Work completed a smoke task but did not expose the invoked plugin version or exact skill-load telemetry. These are not verification of private plugin 0.1.2. The 0.1.2 Desktop invocation in both hosts remains **UNVERIFIED**; no new desktop check was performed for this checker correction. The BigCommerce live sample still did not provide safely associated visible amount, currency, availability, and selected-variant evidence. Gate 2 remains **INCOMPLETE**; rankings and indexation remain unmeasured.

### Same-origin sampler decision

No new bounded same-origin sampler is needed for the documented small explicit sample. `sitemap_discovery.py` provides guarded sitemap discovery and bounded expansion/sample controls; `fetch_page.py` provides guarded retrieval or rendering for selected pages; and `parse_html.py` extracts links from a fetched page for manual same-origin traversal. This supports the workflow in the ecommerce guidance without adding another crawl implementation. It does not constitute a new live-site audit or expand Gate 2 evidence.

## Phase 1 evidence continuation (2026-11-21, DOC-QA-P1-21)

This fresh verification supplements earlier candidate results and supersedes any prior statement that the current candidate's full suite, runtime, or release readiness was complete. The source snapshot was created on WSL ext4 at `/home/zirc/.cache/codex-seo-qa-p1-21/source` from base `9e0101655ba23dd21c2b8afd638e59216a128ead` plus exactly 31 tracked modified paths. The binary tracked patch SHA-256 was `759feeaf22d2da81e1cf1e25d4dacc4ab7c2671a9da963a1b10cb7b18cebe4bc`. Untracked `.venv-posix/` was excluded.

### Source and automated checks

- `python -m pytest tests/ -v -rs`: exit 0; **3,872 passed, 4 skipped, 79 subtests passed**, one WeasyPrint HarfBuzz-Subset deprecation warning, 102.48s. Skips: one WSL case-sensitive-filesystem test and three live GitHub API tests because `CODEX_SEO_NETWORK_TESTS` was unset.
- Supporting QA: cleanup check passed; consistency JSON reported 744 files, 0 errors and 0 warnings; portability JSON reported 40 skills, 0 errors and 0 warnings. Unittest counts: schema 7, cleanup 5, plugin package 17. Documented pytest groups returned 71 passed/3 skipped and 101 passed. Ecommerce/parser/schema dependencies returned 223 passed; metadata 9 passed; no-em-dash 4 passed; plugin package pytest 17 passed/79 subtests. Skill synchronization passed for 76 files.
- Plugin archive build included 79 files; ZIP integrity passed; SHA-256 `ac69c8e0c792d07b3a47c2c40a847e115f652ac1df989725ebf84f6baf129a54`.
- Isolated network tests were run separately. `wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_ENTERPRISE_TOKEN CODEX_SEO_NETWORK_TESTS=1 PYTHONDONTWRITEBYTECODE=1 /home/zirc/.cache/codex-seo-phase1-wsl-20261120/venv/bin/python -m pytest tests/test_sync_flow.py -q -k dry_run` exited 0: 7 passed, 2 skipped, 23 deselected, 22.00s. A follow-up with `-vv -rs -k dry_run` exited 0: 6 passed, 3 skipped, 23 deselected, 0.85s; all three live API tests skipped on HTTP 403 GitHub rate limiting for `docs/01-framework/flow-framework.md`. Preserve both outcomes as observed; live API checks are not recorded as passing.

### Isolated runtime and extension checks

Runtime/browser QA used task-local cache `/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data`, `CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12` (Python 3.12.16), isolated Node v26.13.1 and existing isolated system-library paths, without system installs. An earlier wrapper invocation failed before setup due to inherited Windows PATH/Bash parsing; an earlier setup attempt stopped during Chromium download. The initial QA1 isolated-PATH run completed setup and doctor successfully; it returned 1 of 66 truncated updates and HTTP 200 for raw and rendered pages. Its rendered Chromium timing was 1.568s, with `sandbox=true` and no console errors. The later exact command-specific rerun below supersedes that timing with 1.587s. Logs are under `/home/zirc/.cache/codex-seo-qa-p1-21/logs/`: `runtime_setup_retry.log`, `runtime_doctor.log`, `runtime_updates.log`, `runtime_render_auto.log`, and `runtime_render_always.log`.

On disposable QA-cache paths, the exact Shopify wrapper checks passed: install; checkout rename with relative guide links; repeat install reported already installed; `--create-shopify-env` created an example-matching mode-600 placeholder; a nonsecret sentinel survived rerun; uninstall removed the skill while preserving the guide. The QA transcript contains the exact commands; no lifecycle log file was retained. Artifacts are in the QA cache.

### Current gates and release scope

- The BigCommerce checker did not safely associate visible amount, currency, and availability with the structured Offer or a selected variant. Ecommerce Gate 2 remains **INCOMPLETE**. No ranking or indexing claim is made.
- Candidate 0.1.2 desktop invocation remains **UNVERIFIED**. ChatGPT Work did not expose the current plugin version; Codex Desktop cache showed 0.1.1, not 0.1.2. Phase 1 sign-off is therefore **INCOMPLETE** despite the local checks above.
- The user chose to stop at the existing private plugin release. Public plugin-directory submission is **NOT AUTHORIZED**; existing plugin remains private v0.1.2. Do not upload or submit it.
- The user selected an independent public source repository, `doofx0071/codex-seo`. Repository creation was verified (`fork=false`, default branch `main`, size 0); the source push is pending. The prior `helx0071/codex-seo` repository must remain untouched.
- Phase 2 is **PAUSED**. Do not start additional Phase 2 work under this scope. Preserve Claude-SEO / AgriciDaniel attribution.

No protected Git action, external write, plugin release, public submission, or site write was performed in this documentation continuation. The source push remains pending; this continuation has now been recorded.

### Recorded supporting/package invocations for DOC-QA-P1-21

The following command headers were retained in QA evidence. They ran against the isolated source snapshot described above; results are listed in the preceding evidence section.

```bash
python scripts/check_codex_cleanup.py
python scripts/consistency_check.py --json
python scripts/portability_check.py --json
python -m unittest discover -s tests -p test_schema_validator_cli.py -v
python -m unittest discover -s tests -p test_codex_cleanup.py -v
python -m unittest discover -s tests -p test_plugin_package.py -v
python -m pytest tests/test_codex_agent_configs.py tests/test_agent_mcp_permissions.py tests/test_sync_flow.py tests/test_shopify_crawl.py -q
python -m pytest tests/test_manifest_consistency.py tests/test_pyproject_metadata.py tests/test_hosted_plugin_layout.py tests/test_runtime_installers.py tests/test_manual_install_layout.py tests/test_extension_mirrors.py tests/test_extension_installer_injection.py tests/test_banana_install_layout.py tests/test_banana_key_masking.py tests/test_dataforseo_tool_names.py tests/test_consistency_check.py tests/test_portability.py tests/test_ai_crawler_claims.py -q
python -m pytest tests/test_ecommerce_page_check.py tests/test_parse_html_extraction.py tests/test_parse_html_stdin_url.py tests/test_parse_html_size_cap.py tests/test_parse_html_rel_case.py tests/test_parse_html_malformed_urls.py tests/test_parse_html_inline_spacing.py tests/test_schema_graph_semantics.py tests/test_schema_validator_detection.py tests/test_schema_validator_policy.py tests/test_schema_validator_redos.py tests/test_schema_malformed_offers.py tests/test_schema_v2.py -q
python -m pytest tests/test_pyproject_metadata.py tests/test_manifest_consistency.py -q
python -m pytest tests/test_no_em_dash.py -q
python -m pytest tests/test_plugin_package.py -q
python scripts/sync_codex_skill.py --check
python scripts/build_plugin.py --output dist/codex-seo-plugin.zip
python -m zipfile -t dist/codex-seo-plugin.zip
python -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("dist/codex-seo-plugin.zip").read_bytes()).hexdigest())'
```

The successful isolated runtime checks used this exact WSL/environment prefix for each launcher command:

```bash
wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u CODEX_SEO_NETWORK_TESTS CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data PATH=/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin:/home/zirc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data/ms-playwright PYTHONDONTWRITEBYTECODE=1 ./scripts/codex-seo setup
wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u CODEX_SEO_NETWORK_TESTS CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data PATH=/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin:/home/zirc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data/ms-playwright PYTHONDONTWRITEBYTECODE=1 ./scripts/codex-seo doctor --json
wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u CODEX_SEO_NETWORK_TESTS CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data PATH=/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin:/home/zirc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data/ms-playwright PYTHONDONTWRITEBYTECODE=1 ./scripts/codex-seo run seo_updates.py --limit 1 --json
wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u CODEX_SEO_NETWORK_TESTS CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data PATH=/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin:/home/zirc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data/ms-playwright PYTHONDONTWRITEBYTECODE=1 ./scripts/codex-seo run render_page.py https://example.com --mode auto --json
wsl.exe -d Ubuntu-24.04 --cd /home/zirc/.cache/codex-seo-qa-p1-21/source -- env -u CODEX_SEO_NETWORK_TESTS CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data PATH=/home/zirc/.cache/codex-seo-p1-limits-20261121/node/bin:/home/zirc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LD_LIBRARY_PATH=/home/zirc/.cache/codex-seo-phase1-wsl-20261120/system-libs/usr/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data/ms-playwright PYTHONDONTWRITEBYTECODE=1 ./scripts/codex-seo run render_page.py https://example.com --mode always --json
```

Each invocation exited 0. Setup completed. Doctor reported `ready=true`, `browser_ready=true`, Python 3.12 and runtime 2.6.2. Updates returned 1 of 66 and were truncated. Auto render returned HTTP 200 raw; always render returned HTTP 200 in Playwright Chromium with `sandbox=true`, 1.587s, and no console errors. The environment used Python 3.12.16 and isolated Node v26.13.1. Earlier inherited Windows PATH/Bash parsing failed before setup, and an earlier setup attempt stopped during Chromium download; these failed/incomplete attempts remain distinct from the successful retry. Result logs: `/home/zirc/.cache/codex-seo-qa-p1-21/logs/runtime_setup_retry.log`, `runtime_doctor.log`, `runtime_updates.log`, `runtime_render_auto.log`, and `runtime_render_always.log`.

### Recorded Shopify wrapper invocations

QA transcript commands and assertions (all paths are disposable QA-cache paths; the `.shopify-env` content was a nonsecret sentinel):

```bash
cd /home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b && env CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data ./extensions/shopify/install.sh
/home/zirc/.local/bin/python3.12 -c "from pathlib import Path; old=Path('/home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b'); new=old.with_name('lifecycle-wrapper-qa21b-renamed'); assert old.is_dir() and not new.exists(); old.rename(new); skill=new/'.agents/skills/seo-shopify/SKILL.md'; line=next(x for x in skill.read_text().splitlines() if '[extension guide]' in x); target=(skill.parent/line.split('(',1)[1].split(')',1)[0]).resolve(); print(f'renamed={new}; relative_guide={target}; exists={target.is_file()}'); assert target.is_file()"
cd /home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b-renamed && env CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data ./extensions/shopify/install.sh
cd /home/zirc/.cache/codex-seo-qa-p1-21/shopify-placeholder-wrapper-qa21b && env CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data /home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b-renamed/extensions/shopify/install.sh --create-shopify-env
/home/zirc/.local/bin/python3.12 -c "from pathlib import Path; p=Path('/home/zirc/.cache/codex-seo-qa-p1-21/shopify-placeholder-wrapper-qa21b/.shopify-env'); p.write_text('PLACEHOLDER_SENTINEL=do-not-overwrite\\n'); p.chmod(0o600); print('set nonsecret sentinel in disposable placeholder')"
cd /home/zirc/.cache/codex-seo-qa-p1-21/shopify-placeholder-wrapper-qa21b && env CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data /home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b-renamed/extensions/shopify/install.sh --create-shopify-env
wsl.exe -d Ubuntu-24.04 -- sh -c "grep -Fx PLACEHOLDER_SENTINEL=do-not-overwrite /home/zirc/.cache/codex-seo-qa-p1-21/shopify-placeholder-wrapper-qa21b/.shopify-env; stat -c '%a' /home/zirc/.cache/codex-seo-qa-p1-21/shopify-placeholder-wrapper-qa21b/.shopify-env"
cd /home/zirc/.cache/codex-seo-qa-p1-21/lifecycle-wrapper-qa21b-renamed && env CODEX_SEO_PYTHON=/home/zirc/.local/bin/python3.12 CODEX_SEO_DATA_DIR=/home/zirc/.cache/codex-seo-qa-p1-21/runtime-data ./extensions/shopify/uninstall.sh
```

The final assertion that the installed skill was absent while its guide remained present passed, but its exact Python command was not retained in the QA transcript. The invocation is therefore unavailable and is not reconstructed here.

## Independent source publication verification (2026-11-21, DOC-PUSH-25)

Commit `aa2affa229ce6b533b2741622bb7157de1923f40` (`Prepare independent Codex SEO source release`) was pushed successfully to `https://github.com/doofx0071/codex-seo.git` with `git push https://github.com/doofx0071/codex-seo.git HEAD:refs/heads/main` (exit 0); the preceding dry-run passed. GitHub API verification reports `fork=false`, `private=false`, and `default_branch=main`. Both `git ls-remote` and `gh api repos/doofx0071/codex-seo/commits/main` returned the same commit SHA. The README is visible on `main` with size 3,226 bytes. At the time checked, `gh api repos/doofx0071/codex-seo/actions/runs` returned `total_count=0`; no CI or GitHub Actions run is evidenced as passing. The repository API's reported `size=0` is not treated as evidence of missing content because the README and commit endpoints verify the published source.

The local `origin` points to `doofx0071/codex-seo`; `legacy-fork` preserves both `helx0071` URLs. Local `main` tracks `origin/main`, and both point to `aa2affa229ce6b533b2741622bb7157de1923f40`. `codex-native-support` remains preserved and was not pushed to the new repository. The earlier `helx0071/codex-seo` repository was not modified. Untracked `.venv-posix/` remains preserved, and the separate `C:\dev\worktrees\ecommerce-visible-facts\codex-seo` worktree was untouched. The new repository was empty before this direct source publication, so no pull request or merge was involved. Claude-SEO / AgriciDaniel attribution and notices remain preserved.

This completes source publication only. The existing plugin remains private v0.1.2; public plugin-directory submission is **NOT AUTHORIZED**. Candidate 0.1.2 desktop smoke remains **UNVERIFIED**. Ecommerce Gate 2 and Phase 1 sign-off remain **INCOMPLETE**. Phase 2 remains **PAUSED**. No plugin publication or Phase 1 completion is implied.

## Hosted CI follow-up (2026-11-21, CI-LINT-26)

The earlier `total_count=0` Actions observation above was accurate at that time. A later query, `gh api repos/doofx0071/codex-seo/actions/runs --jq '.workflow_runs[] | {id, name: .name, event, status, conclusion, head_branch, head_sha, created_at, html_url}'`, returned 13 run records. The push-triggered `CI` run `44905702787` for `main` at `aa2affa229ce6b533b2741622bb7157de1923f40` completed with `failure` (`https://github.com/doofx0071/codex-seo/actions/runs/44905702787`). `gh run view 44905702787 --log-failed` identified the failing `Lint with ruff` step: it installed `ruff==0.17.1`, then `ruff check .` exited 1 with four findings: I001 import ordering in `scripts/ecommerce_page_check.py`, `tests/test_agent_mcp_permissions.py`, and `tests/test_codex_cleanup.py`; F401 for unused `os` in `tests/test_matomo_report.py`.

The findings were reproduced and fixed as import-only changes on local branch `codex/ci-lint-26` in isolated worktree `C:\dev\worktrees\codex-seo-ci-lint-20261121`, commit `104a48778653efac54a471bc1d0421d3cc8b361e` (`style: satisfy Ruff CI checks`). No behavior changed. In the task-local WSL Ubuntu-24.04 environment with Python 3.12.16, fresh `ruff check .` returned exit 0 (`All checks passed!`); `python -m pytest tests/test_agent_mcp_permissions.py tests/test_codex_cleanup.py tests/test_matomo_report.py tests/test_ecommerce_page_check.py -q` returned **83 passed**; and `git diff --check` passed. The full pytest suite was not rerun for this import-only change. The preceding 3,872 passed / 4 skipped / 79 subtests result is baseline evidence for commit `aa2affa`, not a rerun of `104a487`.

At the time this status was first recorded, commit `104a487` had been fast-forwarded into local `main` but not pushed; `origin/main` was still at `aa2affa229ce6b533b2741622bb7157de1923f40`, and the fix had no hosted CI result. That interim state was superseded by the successful push and hosted rerun recorded below. This does not change Phase 1 status: candidate 0.1.2 desktop smoke remains **UNVERIFIED**, Gate 2 and Phase 1 remain **INCOMPLETE**, and Phase 2 remains **PAUSED**.

An auxiliary `wsl.exe -d Ubuntu-24.04 --cd /mnt/c/dev/worktrees/codex-seo-ci-lint-20261121 -- /home/zirc/.cache/codex-seo-ci-lint-20261121/venv/bin/python -m pytest tests/test_no_em_dash.py -q` attempt returned **1 failed, 3 passed**. The failing test did not reach its text assertion: its `git ls-files` subprocess exited 128 because WSL Git could not resolve the Windows-format `.git` pointer in this mounted linked worktree (`C:/dev/codex-seo/.git/worktrees/codex-seo-ci-lint-20261121`). This check is **UNAVAILABLE** for this worktree environment, not a content failure. A separate direct PowerShell scan of the updated verification document for U+2014 exited 0 and found no em dash. No global Git setting was changed.

## Hosted CI successful rerun (2026-11-21, CI-LINT-26-RESULTS)

The reviewed source commit was pushed to `origin/main` with `git push origin main` (exit 0), advancing `main` from `aa2affa229ce6b533b2741622bb7157de1923f40` to `104a48778653efac54a471bc1d0421d3cc8b361e`. `git ls-remote origin refs/heads/main` and `gh api repos/doofx0071/codex-seo/commits/main --jq '.sha'` both returned `104a48778653efac54a471bc1d0421d3cc8b361e`.

GitHub Actions run [44908215381](https://github.com/doofx0071/codex-seo/actions/runs/44908215381) for push event on `main` at `104a48778653efac54a471bc1d0421d3cc8b361e` completed with conclusion `success`; all 12 jobs passed: Python syntax and lint, secret scan, dependency audits for Python 3.11 and 3.14, test suites for Python 3.11, 3.12 and 3.14, portability on Windows and macOS, and browser guards on Ubuntu, Windows and macOS. This successful hosted workflow verifies commit `104a487` and resolves the earlier hosted Ruff failure. It does not verify the local documentation edits in this file, which were made after the source push.

The private plugin remains v0.1.2 and public plugin-directory submission remains **NOT AUTHORIZED**. Candidate 0.1.2 desktop smoke is **UNVERIFIED**; ecommerce Gate 2 and Phase 1 sign-off remain **INCOMPLETE**; Phase 2 remains **PAUSED**. The earlier `helx0071/codex-seo` repository, `.venv-posix/`, and separate ecommerce worktree remain untouched.
