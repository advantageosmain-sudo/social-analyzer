#!/usr/bin/env node
/**
 * product-readiness-check — verifies that the social-analyzer product in this
 * repository is actually runnable and sellable in the current environment.
 *
 * Read-only against the product: it never edits upstream files, never
 * publishes, never spends. It writes a JSON + Markdown report to
 * agents/workspace/10_Engagements/_readiness/ (or --out).
 *
 * Usage: node agents/skills/product-readiness-check/run.mjs [--out DIR] [--skip-network] [--skip-gui]
 */
import { execFileSync, spawn } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import https from 'node:https'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import semver from 'semver'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO = path.resolve(__dirname, '..', '..', '..')
const require = createRequire(path.join(REPO, 'package.json'))
const args = process.argv.slice(2)
const flag = (n) => args.includes(n)
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d }
const OUT = path.resolve(opt('--out', path.join(REPO, 'agents', 'workspace', '10_Engagements', '_readiness')))
const CA = '/etc/ssl/certs/ca-certificates.crt'

const results = []
const add = (id, area, status, detail, remediation = '') => {
  results.push({ id, area, status, detail, remediation })
  const tag = { PASS: '✅', WARN: '⚠️ ', FAIL: '❌', SKIP: '⏭️ ' }[status]
  console.log(`${tag} [${area}] ${id}: ${detail}${remediation && status !== 'PASS' ? `\n      ↳ ${remediation}` : ''}`)
}
const sh = (cmd, cmdArgs, extra = {}) => execFileSync(cmd, cmdArgs, { cwd: REPO, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 60000, ...extra })
const which = (bin) => { try { return sh('which', [bin]).trim() } catch { return null } }

// ---------------------------------------------------------------- runtime
const pkg = JSON.parse(readFileSync(path.join(REPO, 'package.json'), 'utf8'))
const want = pkg.engines?.node || '*'
if (semver.satisfies(process.version, want)) add('node-version', 'runtime', 'PASS', `node ${process.version} satisfies engines ${want}`)
else add('node-version', 'runtime', 'FAIL', `node ${process.version} does not satisfy engines ${want}`, 'Install a matching Node release (nvm/n).')

const missing = Object.keys(pkg.dependencies).filter((d) => { try { require.resolve(d + '/package.json') } catch { try { require.resolve(d) } catch { return true } } return false })
if (missing.length === 0) add('npm-deps', 'runtime', 'PASS', `all ${Object.keys(pkg.dependencies).length} runtime dependencies resolvable`)
else add('npm-deps', 'runtime', 'FAIL', `missing: ${missing.join(', ')}`, 'npm install --ignore-scripts (geckodriver postinstall needs direct GitHub TLS).')

// ---------------------------------------------------------------- data
for (const f of ['sites.json', 'languages.json', 'names.json', 'countries.json', 'dict.json']) {
  const fp = path.join(REPO, 'data', f)
  try {
    const j = JSON.parse(readFileSync(fp, 'utf8'))
    const n = Array.isArray(j) ? j.length : (Array.isArray(j.websites_entries) ? j.websites_entries.length : Object.keys(j).length)
    add(`data-${f}`, 'data', 'PASS', `${f} parses (${n} entries)`)
  } catch (e) { add(`data-${f}`, 'data', 'FAIL', `${f}: ${e.message}`, 'Restore from upstream qeeqbox/social-analyzer.') }
}
try {
  const a = readFileSync(path.join(REPO, 'data', 'sites.json'))
  const b = readFileSync(path.join(REPO, 'data', 'sites.json_new'))
  add('data-sites-drift', 'data', a.equals(b) ? 'PASS' : 'WARN', a.equals(b) ? 'sites.json_new identical to sites.json' : 'sites.json_new differs from sites.json', 'Review pending detection updates before release.')
} catch { /* optional */ }

// ---------------------------------------------------------------- cli
try {
  const out = sh('node', ['app.js', '--help'])
  add('cli-help', 'cli', out.includes('--username') ? 'PASS' : 'FAIL', 'node app.js --help prints usage')
} catch (e) { add('cli-help', 'cli', 'FAIL', `node app.js --help failed: ${e.stderr || e.message}`) }
try {
  const out = sh('python3', ['app.py', '-h'])
  add('py-cli-help', 'cli', out.includes('--username') ? 'PASS' : 'WARN', 'python3 app.py -h prints usage')
} catch (e) { add('py-cli-help', 'cli', 'WARN', `python CLI unavailable: ${(e.stderr || e.message).split('\n')[0]}`, 'pip3 install -r requirements.txt (optional — Node path is primary).') }

// ---------------------------------------------------------------- tls / network
const probe = (ca) => new Promise((resolve) => {
  const o = { host: 'github.com', path: '/', method: 'HEAD', timeout: 8000 }
  if (ca && existsSync(ca)) o.ca = readFileSync(ca)
  const r = https.request(o, (res) => { res.resume(); resolve({ ok: true, code: res.statusCode }) })
  r.on('error', (e) => resolve({ ok: false, err: e.code || e.message }))
  r.on('timeout', () => { r.destroy(); resolve({ ok: false, err: 'timeout' }) })
  r.end()
})
let needsCA = false
if (flag('--skip-network')) add('tls-default', 'network', 'SKIP', 'network checks skipped')
else {
  const d = await probe(null)
  if (d.ok) add('tls-default', 'network', 'PASS', `HTTPS to github.com works with Node default CA (HTTP ${d.code})`)
  else {
    const withCA = await probe(CA)
    needsCA = withCA.ok
    if (withCA.ok) add('tls-default', 'network', 'WARN', `Node default CA fails (${d.err}); works with system bundle`, `Run scans with NODE_EXTRA_CA_CERTS=${CA} (TLS interception / corporate proxy environment).`)
    else add('tls-default', 'network', 'FAIL', `HTTPS to github.com fails: ${d.err} / ${withCA.err}`, 'No outbound HTTPS — scans cannot run here.')
  }
}

// ---------------------------------------------------------------- live scan smoke
if (flag('--skip-network')) add('scan-smoke', 'product', 'SKIP', 'scan skipped')
else {
  try {
    const env = { ...process.env }
    if (needsCA) env.NODE_EXTRA_CA_CERTS = CA
    const out = sh('node', ['app.js', '--username', 'johndoe', '--websites', 'github', '--output', 'json', '--options', 'link,rate', '--profiles', 'all', '--filter', 'all'], { env, timeout: 120000 })
    const j = JSON.parse(out.slice(out.indexOf('{'), out.lastIndexOf('}') + 1))
    const det = (j.detected || []).length
    add('scan-smoke', 'product', det > 0 ? 'PASS' : 'FAIL', det > 0 ? `fast scan detected ${det} profile(s) for johndoe@github` : `fast scan returned no detection: ${JSON.stringify(j).slice(0, 200)}`, det > 0 ? '' : 'Check network egress and data/sites.json detections.')
  } catch (e) { add('scan-smoke', 'product', 'FAIL', `scan crashed: ${(e.stderr || e.message).split('\n')[0]}`) }
}

// ---------------------------------------------------------------- optional capabilities
const ff = which('firefox') || which('firefox-esr')
add('slow-scan-firefox', 'optional', ff ? 'PASS' : 'WARN', ff ? `firefox at ${ff}` : 'firefox not installed — --mode slow (webdriver) unavailable', 'apt-get install firefox-esr; or run via docker-compose grid.')
const gecko = existsSync(path.join(REPO, 'node_modules', 'geckodriver', 'lib', 'geckodriver')) || which('geckodriver')
add('slow-scan-geckodriver', 'optional', gecko ? 'PASS' : 'WARN', gecko ? 'geckodriver present' : 'geckodriver binary missing (postinstall skipped/failed)', 'npm rebuild geckodriver with working TLS to github.com.')
const tess = which('tesseract')
add('ocr-tesseract', 'optional', tess ? 'PASS' : 'WARN', tess ? `tesseract at ${tess}` : 'tesseract not installed — OCR detection layer disabled', 'apt-get install tesseract-ocr.')

// ---------------------------------------------------------------- gui
if (flag('--skip-gui')) add('gui-start', 'product', 'SKIP', 'gui skipped')
else {
  const http = (await import('node:http')).default
  const r = await new Promise((resolve) => {
    const p = spawn('node', ['app.js', '--gui'], { cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'] })
    let log = ''
    let settled = false
    const done = (v) => { if (settled) return; settled = true; try { p.kill('SIGTERM') } catch {} resolve(v) }
    p.stdout.on('data', (d) => { log += d })
    p.stderr.on('data', (d) => { log += d })
    const t0 = Date.now()
    const tick = () => {
      http.get('http://localhost:9005/get_settings', (res) => { res.resume(); done({ ok: res.statusCode === 200, code: res.statusCode }) })
        .on('error', () => { if (Date.now() - t0 > 20000) done({ ok: false, err: 'timeout', log }); else setTimeout(tick, 500) })
    }
    setTimeout(tick, 800)
    p.on('exit', (c) => done({ ok: false, err: `exited ${c}`, log }))
  })
  add('gui-start', 'product', r.ok ? 'PASS' : 'FAIL', r.ok ? 'GUI served /get_settings on :9005' : `GUI did not come up: ${r.err} ${(r.log || '').slice(-200)}`, r.ok ? '' : 'Port 9005 busy or startup error; see logs/.')
}

// ---------------------------------------------------------------- source of truth
try {
  const status = sh('git', ['status', '--porcelain']).trim()
  const branch = sh('git', ['rev-parse', '--abbrev-ref', 'HEAD']).trim()
  const dirtyUpstream = status.split('\n').filter(Boolean).filter((l) => !/ agents\//.test(l) && !/ agents\/$/.test(l.trim()))
  add('git-branch', 'records', 'PASS', `on ${branch}; ${status ? status.split('\n').length + ' changed path(s)' : 'clean tree'}`)
  add('upstream-files-untouched', 'records', dirtyUpstream.length ? 'WARN' : 'PASS', dirtyUpstream.length ? `upstream files modified: ${dirtyUpstream.slice(0, 5).join(' | ')}` : 'no upstream (non-agents/) files modified in working tree', 'Keep product changes in reviewed commits; agents/ is the only fork-owned area.')
} catch (e) { add('git-branch', 'records', 'WARN', `git unavailable: ${e.message}`) }
const wf = path.join(REPO, '.github', 'workflows', 'main.yml')
if (existsSync(wf)) {
  const y = readFileSync(wf, 'utf8')
  const auto = /git push/.test(y) && /on:\s*\[push\]/.test(y)
  add('ci-autocommit', 'records', auto ? 'WARN' : 'PASS', auto ? 'upstream workflow auto-commits & pushes on every push (qeeqbox auto-checking.sh)' : 'no auto-push workflow', 'This is upstream tooling, not an owner gate. Disable in fork settings or keep Actions off for this repo if you do not want unattended commits.')
}

// ---------------------------------------------------------------- summary
const counts = results.reduce((m, r) => (m[r.status] = (m[r.status] || 0) + 1, m), {})
const verdict = counts.FAIL ? 'NOT READY' : counts.WARN ? 'READY WITH CAVEATS' : 'READY'
const report = { product: 'social-analyzer', version: pkg.version, generated: new Date().toISOString(), node: process.version, verdict, counts, results }
mkdirSync(OUT, { recursive: true })
writeFileSync(path.join(OUT, 'readiness.json'), JSON.stringify(report, null, 2))
const md = [`# Product readiness — social-analyzer ${pkg.version}`, '', `Generated: ${report.generated}  ·  Node ${process.version}`, '', `**Verdict: ${verdict}**  (${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(', ')})`, '', '| Area | Check | Status | Detail | Remediation |', '|---|---|---|---|---|',
  ...results.map((r) => `| ${r.area} | ${r.id} | ${r.status} | ${r.detail.replace(/\|/g, '\\|')} | ${r.remediation.replace(/\|/g, '\\|')} |`), '',
  '_Read-only check. No upstream files, settings or external services were modified. Owner approval gates unchanged._'].join('\n')
writeFileSync(path.join(OUT, 'readiness.md'), md)
console.log(`\nVerdict: ${verdict} — report written to ${path.relative(REPO, OUT)}/readiness.{json,md}`)
process.exit(counts.FAIL ? 1 : 0)
