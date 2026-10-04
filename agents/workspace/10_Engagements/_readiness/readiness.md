# Product readiness — social-analyzer 2.0.32

Generated: 2026-10-04T14:52:32.127Z  ·  Node v22.22.3

**Verdict: READY WITH CAVEATS**  (PASS 14, WARN 5)

| Area | Check | Status | Detail | Remediation |
|---|---|---|---|---|
| runtime | node-version | PASS | node v22.22.3 satisfies engines >=20.18.1 |  |
| runtime | npm-deps | PASS | all 28 runtime dependencies resolvable |  |
| data | data-sites.json | PASS | sites.json parses (999 entries) |  |
| data | data-languages.json | PASS | languages.json parses (184 entries) |  |
| data | data-names.json | PASS | names.json parses (50 entries) |  |
| data | data-countries.json | PASS | countries.json parses (242 entries) |  |
| data | data-dict.json | PASS | dict.json parses (3 entries) |  |
| data | data-sites-drift | PASS | sites.json_new identical to sites.json | Review pending detection updates before release. |
| cli | cli-help | PASS | node app.js --help prints usage |  |
| cli | py-cli-help | PASS | python3 app.py -h prints usage |  |
| network | tls-default | WARN | Node default CA fails (UNABLE_TO_VERIFY_LEAF_SIGNATURE); works with system bundle | Run scans with NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt (TLS interception / corporate proxy environment). |
| product | scan-smoke | PASS | fast scan detected 1 profile(s) for johndoe@github |  |
| optional | slow-scan-firefox | WARN | firefox not installed — --mode slow (webdriver) unavailable | apt-get install firefox-esr; or run via docker-compose grid. |
| optional | slow-scan-geckodriver | WARN | geckodriver binary missing (postinstall skipped/failed) | npm rebuild geckodriver with working TLS to github.com. |
| optional | ocr-tesseract | WARN | tesseract not installed — OCR detection layer disabled | apt-get install tesseract-ocr. |
| product | gui-start | PASS | GUI served /get_settings on :9005 |  |
| records | git-branch | PASS | on arena/01a10754-social-analyzer; 1 changed path(s) |  |
| records | upstream-files-untouched | PASS | no upstream (non-agents/) files modified in working tree | Keep product changes in reviewed commits; agents/ is the only fork-owned area. |
| records | ci-autocommit | WARN | upstream workflow auto-commits & pushes on every push (qeeqbox auto-checking.sh) | This is upstream tooling, not an owner gate. Disable in fork settings or keep Actions off for this repo if you do not want unattended commits. |

_Read-only check. No upstream files, settings or external services were modified. Owner approval gates unchanged._