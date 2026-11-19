# Run with Git Bash and supported Python available on PATH.
$ErrorActionPreference = "Stop"
$Launcher = Join-Path $PSScriptRoot "../../scripts/codex-seo"
$Extension = Split-Path -Leaf $PSScriptRoot
& bash ($Launcher.Replace('\', '/')) run extension_install.py install $Extension @args
exit $LASTEXITCODE
