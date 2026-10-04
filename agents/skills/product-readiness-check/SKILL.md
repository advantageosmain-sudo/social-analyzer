# Skill: product-readiness-check

**Area:** Product Readiness · **Owner approval gates touched:** none (read-only) · **Status:** implemented & tested

## Purpose
Answer one question with evidence: *can the social-analyzer product in this repository actually be run and sold from this environment right now?* It checks runtime, data, CLI, network/TLS, a live detection, the GUI, optional detection layers, and source-of-truth hygiene, then writes a dated report.

## Reuses (does not duplicate)
- `app.js` CLI and GUI, `data/*.json`, `package.json` engines — exercised as-is.
- `semver` (already a runtime dependency) for the engine check.

## Instructions
```bash
node agents/skills/product-readiness-check/run.mjs            # full check (~5–25 s)
node agents/skills/product-readiness-check/run.mjs --skip-network --skip-gui   # offline/CI-safe subset
node agents/skills/product-readiness-check/run.mjs --out /path/to/dir
```
Output: `agents/workspace/10_Engagements/_readiness/readiness.json` and `readiness.md`.
Exit code `0` = READY or READY WITH CAVEATS; `1` = NOT READY (at least one FAIL).

Interpretation:
| Verdict | Action |
|---|---|
| READY | proceed with production |
| READY WITH CAVEATS | proceed in fast mode; apply listed remediations before promising slow-mode/OCR features |
| NOT READY | stop; fix FAIL items; re-run |

## Permission boundaries
- MAY: read repo files, resolve node modules, spawn `node app.js` (help, one fast scan of `johndoe@github`, GUI on :9005 for ≤20 s), make one HTTPS HEAD to github.com, run `git status`.
- MAY NOT: modify any file outside `agents/workspace/`, install packages, change settings, call paid APIs, push, publish, or communicate externally.
- Network use is limited to the smoke scan; pass `--skip-network` in restricted environments.

## Verification example (run 2026-10-04 in the Arena sandbox)
```
✅ node-version: node v22.22.3 satisfies engines >=20.18.1
✅ npm-deps: all 28 runtime dependencies resolvable
✅ data-sites.json: sites.json parses (999 entries)
⚠️  tls-default: Node default CA fails (UNABLE_TO_VERIFY_LEAF_SIGNATURE); works with system bundle
      ↳ Run scans with NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
✅ scan-smoke: fast scan detected 1 profile(s) for johndoe@github
⚠️  slow-scan-firefox / slow-scan-geckodriver / ocr-tesseract: not installed → fast mode only
✅ gui-start: GUI served /get_settings on :9005
✅ upstream-files-untouched: no upstream (non-agents/) files modified
⚠️  ci-autocommit: upstream workflow auto-commits & pushes on every push
Verdict: READY WITH CAVEATS
```
The TLS caveat was a real find: without it every scan in this environment reports `failed`.

## Invocation prompt
> Run the product-readiness-check skill on this repository, then summarise the verdict, every WARN/FAIL with its remediation, and tell me whether we can promise slow-mode (webdriver) and OCR detection to customers this week. Do not change any product files.
