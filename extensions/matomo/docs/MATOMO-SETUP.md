# Matomo extension setup

## What this gives you

1. **Matomo Reporting API** for organic traffic, landing pages, devices,
   countries, referrers, and search keywords via
   `./scripts/codex-seo run matomo_report.py`.
2. **Live credential probe** via `./scripts/codex-seo run matomo_auth.py --check`
   used by the `$seo matomo` skill and the audit orchestrator.
3. An optional `seo-matomo` checkout skill and a role prompt for inline
   analysis during `$seo audit`.

## Install

From the Codex SEO checkout with its [managed runtime](../../../docs/INSTALLATION.md) set up:

```text
./extensions/matomo/install.sh
# Windows PowerShell (Git Bash must be on PATH)
.\extensions\matomo\install.ps1
```

This registers the optional checkout skill under `.agents/skills/`. Open a new Codex session to discover it.

Set `MATOMO_URL`, `MATOMO_API_TOKEN`, and optionally `MATOMO_SITE_ID` in the environment that starts the local runtime. For a stored profile, set `CODEX_SEO_PROFILE_DIR` to a dedicated absolute path outside the repository, or use `~/.config/codex-seo/`. Put a private `matomo.json` in that directory with `matomo_url`, `matomo_token`, and optionally `matomo_site_id`. Use owner-only permissions, or a per-user ACL on Windows. Restart Codex after changing its launch environment.

## Least-privilege token setup

1. Use a dedicated Matomo account with **View** access only to the sites you
   intend to analyze. Do not use an Admin or Superuser account for routine
   reporting.
2. Go to **Administration -> Personal -> Security -> API Tokens** and create
   a token with a clear name such as `codex-seo`.
3. In Matomo 6, set the token access level to **View** and enable **Only allow
   secure requests**. The client sends the token in the POST body, so POST-only
   tokens are compatible. Use an HTTPS `MATOMO_URL` to protect credentials in
   transit; HTTP remains available for explicitly configured private instances.
4. In Matomo 5, tokens inherit the creator's account permissions. Create and
   use a dedicated View-only account before generating the token.
5. Copy the generated `token_auth`. Matomo only shows it once at creation.

Keep the token in the environment or private profile described above, never in
the repository or a chat message. The `--setup` command prints these
instructions; it does not create or store credentials.

## Self-hosted instance on a private address

Every request to your Matomo instance goes through codex-seo's shared SSRF
guard, the `url_safety` module: the instance URL is validated, its hostname is
pinned to the validated address for the life of the request, and a redirect
away from the instance is refused rather than followed.

That guard refuses private, loopback, and link-local addresses by default, so
an instance at `http://matomo.internal:8080`, `http://192.168.1.20`, or
`http://localhost:8080` is refused until you say it is yours. Name it in the
`CODEX_SEO_LOCAL_TARGETS` allowlist:

```bash
export CODEX_SEO_LOCAL_TARGETS="matomo.internal:8080"
```

Entries are `host` or `host:port`, comma-separated, matched exactly. A bare
`host` matches any port on that host; `host:port` matches that port only.
There is no wildcard, no range, and no "allow private" mode. To make it
permanent, configure the environment that launches Codex.

The allowlist is deliberately narrow, and the narrowness is the point:

- It is consulted only for the top-level instance URL. A redirect target or
  any other host stays fail-closed, so a compromised or misconfigured Matomo
  cannot use the allowlist to reach the rest of your network.
- Cloud metadata endpoints (169.254.169.254, `metadata.google.internal`,
  100.100.100.200, and their siblings) are refused even when listed.
- Unset, codex-seo behaves exactly as it does without the feature.

Use `./scripts/codex-seo run matomo_auth.py --local-target-hint <url>` to check the allowlist entry for a private host.

Full semantics: [SECURITY.md](../../../SECURITY.md).

If your Matomo instance requires a self-signed certificate, install its
CA into the system trust store. The script uses `requests` defaults; it
will fail with `SSLError` on untrusted certificates.

## Verify

```bash
./scripts/codex-seo run matomo_auth.py --check
./scripts/codex-seo run matomo_report.py check --json
./scripts/codex-seo run matomo_report.py organic --json
```

`--check` runs `API.getMatomoVersion` against your instance and reports
the Matomo version string. Any 401/403, network error, or Matomo
`result=error` payload is surfaced as a friendly error with remediation
hints.

## Audit integration

When `matomo_auth.py --check` succeeds, the `$seo audit` orchestrator
applies the [Matomo role prompt](../agents/seo-matomo.md) inline. It
writes `output_dir/findings/matomo.md` with the organic traffic trend,
top landing pages, device and country split, and referrer breakdown.
An audit can include both Matomo and GA4 when both are configured.

## Uninstall

Run `./extensions/matomo/uninstall.sh` to remove the checkout skill entry. Remove `MATOMO_URL`, `MATOMO_API_TOKEN`, and `MATOMO_SITE_ID` from the environment you configured. Remove your dedicated Matomo profile file if you no longer use it.
