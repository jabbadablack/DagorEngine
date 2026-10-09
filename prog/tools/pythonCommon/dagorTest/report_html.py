"""report.html: one self-contained file (no external resources) to browse a run, including image comparisons."""
import base64
import json
import os

from .model import RunResult
from .reports import to_json_dict

MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.tga': 'image/x-tga', '.bmp': 'image/bmp'}


def _inline_images(run_dict, run_dir, budget):
  """Image artifacts become data URIs while the budget lasts; the rest stay relative links next to the report."""
  images = {}
  for t in run_dict['targets']:
    for c in t['cases']:
      for a in c['artifacts']:
        for rel in a['files'].values():
          if rel in images:
            continue
          path = os.path.join(run_dir, rel)
          mime = MIME.get(os.path.splitext(rel)[1].lower())
          try:
            size = os.path.getsize(path)
          except OSError:
            continue
          if mime and size <= budget:
            with open(path, 'rb') as f:
              images[rel] = 'data:{};base64,{}'.format(mime, base64.b64encode(f.read()).decode('ascii'))
            budget -= size
  return images


def _tail_logs(run_dict, run_dir, max_bytes):
  logs = {}
  for t in run_dict['targets']:
    rel = t.get('log')
    if not rel or rel in logs:
      continue
    try:
      with open(os.path.join(run_dir, rel), 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        text = f.read().decode('utf-8', 'replace')
      logs[rel] = ('[... {} bytes skipped ...]\n'.format(size - max_bytes) if size > max_bytes else '') + text
    except OSError:
      pass
  return logs


def write_html(run: RunResult, run_dir: str, path: str, image_budget=50 << 20, log_tail=48 << 10):
  data = to_json_dict(run)
  payload = {'run': data, 'images': _inline_images(data, run_dir, image_budget), 'logs': _tail_logs(data, run_dir, log_tail)}
  blob = json.dumps(payload).replace('</', '<\\/')
  html = TEMPLATE.replace('__TITLE__', 'Dagor tests {} - {}'.format(run.run_id, run.status.value)).replace('__DATA__', blob)
  with open(path, 'w', encoding='utf-8') as f:
    f.write(html)


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#fff; --fg:#1d1f23; --muted:#6a7079; --line:#e2e4e8; --panel:#f6f7f9; --pass:#1a7f37; --fail:#cf222e; --skip:#7d8590; --warn:#bf8700; --err:#8250df; --link:#0969da; }
@media (prefers-color-scheme: dark) { :root { --bg:#0e1116; --fg:#e6edf3; --muted:#8d96a0; --line:#2b3138; --panel:#161b22; --pass:#3fb950; --fail:#f85149; --skip:#8d96a0; --warn:#d29922; --err:#a371f7; --link:#4493f8; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
header { padding: 20px 24px; border-bottom: 1px solid var(--line); }
h1 { margin: 0 0 4px; font-size: 20px; }
.meta { color: var(--muted); font-size: 13px; }
.counts { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip { padding: 2px 10px; border-radius: 999px; border: 1px solid var(--line); font-size: 13px; cursor: pointer; user-select: none; background: var(--panel); }
.chip.off { opacity: .35; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 24px; border-bottom: 1px solid var(--line); align-items: center; }
input[type=search], select { background: var(--panel); color: var(--fg); border: 1px solid var(--line); border-radius: 6px; padding: 5px 8px; font: inherit; }
input[type=search] { min-width: 260px; flex: 1; max-width: 480px; }
main { padding: 8px 24px 40px; }
details.target { border: 1px solid var(--line); border-radius: 8px; margin: 8px 0; background: var(--bg); }
details.target > summary { padding: 8px 12px; cursor: pointer; display: flex; gap: 12px; align-items: center; list-style: none; }
details.target > summary::-webkit-details-marker { display: none; }
.st { font-weight: 600; min-width: 64px; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }
.st.passed { color: var(--pass); } .st.failed { color: var(--fail); } .st.timeout { color: var(--warn); } .st.error { color: var(--err); } .st.skipped { color: var(--skip); }
.tid { font-weight: 600; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 13px; overflow-wrap: anywhere; }
.layer, .dur { color: var(--muted); font-size: 12px; }
.dur { margin-left: auto; white-space: nowrap; }
.body { padding: 4px 12px 12px; border-top: 1px solid var(--line); }
.msg { color: var(--fail); white-space: pre-wrap; overflow-wrap: anywhere; font-family: ui-monospace, Consolas, monospace; font-size: 12px; margin: 6px 0; }
.case { border-top: 1px dashed var(--line); padding: 6px 0; }
.case:first-child { border-top: 0; }
.case .head { display: flex; gap: 12px; align-items: baseline; }
.case .name { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; overflow-wrap: anywhere; }
pre { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 8px; overflow: auto; max-height: 420px; font-size: 12px; margin: 6px 0; white-space: pre-wrap; overflow-wrap: anywhere; }
a { color: var(--link); }
.img { margin: 8px 0; border: 1px solid var(--line); border-radius: 6px; padding: 8px; background: var(--panel); }
.img .modes { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; align-items: center; }
.img button { background: var(--bg); color: var(--fg); border: 1px solid var(--line); border-radius: 5px; padding: 2px 8px; cursor: pointer; font: inherit; font-size: 12px; }
.img button.on { border-color: var(--link); color: var(--link); }
.stage { position: relative; display: inline-block; max-width: 100%; image-rendering: pixelated; }
.stage img { display: block; max-width: 100%; }
.stage .over { position: absolute; inset: 0; overflow: hidden; }
.stage .over img { max-width: none; }
.metrics { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
.empty { color: var(--muted); padding: 24px 0; }
</style>
</head>
<body>
<header><h1 id="title"></h1><div class="meta" id="meta"></div><div class="counts" id="counts"></div></header>
<div class="toolbar">
  <input type="search" id="q" placeholder="Filter targets and cases">
  <select id="layer"><option value="">All layers</option></select>
  <label class="meta"><input type="checkbox" id="problemsOnly"> problems only</label>
</div>
<main id="list"></main>
<script id="data" type="application/json">__DATA__</script>
<script>
(function () {
  const payload = JSON.parse(document.getElementById('data').textContent);
  const run = payload.run, images = payload.images, logs = payload.logs;
  const STATUSES = ['failed', 'timeout', 'error', 'passed', 'skipped'];
  const PROBLEM = new Set(['failed', 'timeout', 'error']);
  const shown = new Set(STATUSES);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const src = rel => images[rel] || rel;
  const fmt = s => s < 1 ? (s * 1000).toFixed(0) + ' ms' : s.toFixed(1) + ' s';

  document.getElementById('title').textContent = 'Dagor tests: ' + run.status.toUpperCase();
  document.getElementById('meta').textContent = [run.device + ' on ' + run.platform + '-' + run.arch + ' (' + run.config + ')',
    run.started, fmt(run.duration), run.git_rev ? 'rev ' + run.git_rev : ''].filter(Boolean).join(' · ');

  const totals = {}; STATUSES.forEach(s => totals[s] = 0);
  run.targets.forEach(t => totals[t.status]++);
  const counts = document.getElementById('counts');
  STATUSES.forEach(s => {
    const c = el('span', 'chip st ' + s, s + ': ' + totals[s] + ' target' + (totals[s] == 1 ? '' : 's'));
    c.onclick = () => { shown.has(s) ? shown.delete(s) : shown.add(s); c.classList.toggle('off', !shown.has(s)); render(); };
    counts.appendChild(c);
  });
  const layerSel = document.getElementById('layer');
  [...new Set(run.targets.map(t => t.layer))].sort().forEach(l => layerSel.appendChild(new Option(l, l)));

  function imageViewer(a) {
    const box = el('div', 'img');
    const title = el('div', 'metrics');
    title.textContent = a.name + (a.passed ? ' — matches' : ' — differs') +
      (a.metrics && a.metrics.rms !== undefined ? ' · rms ' + a.metrics.rms.toFixed(3) + ' · bad pixels ' + a.metrics.badPixelsPercent.toFixed(3) + '% · max diff ' + a.metrics.maxChannelDiff : '');
    box.appendChild(title);
    if (a.message) box.appendChild(el('div', 'msg', a.message));
    const roles = ['actual', 'reference', 'diff'].filter(r => a.files[r]);
    if (!roles.length) return box;
    const modes = el('div', 'modes'), stage = el('div', 'stage');
    const base = el('img'); stage.appendChild(base);
    const over = el('div', 'over'), overImg = el('img'); over.appendChild(overImg);
    const slider = document.createElement('input'); slider.type = 'range'; slider.min = 0; slider.max = 100; slider.value = 50;
    let mode = roles.includes('diff') ? 'diff' : roles[0];
    const set = m => {
      mode = m;
      [...modes.querySelectorAll('button')].forEach(b => b.classList.toggle('on', b.dataset.m == m));
      if (m == 'slider') { base.src = src(a.files.reference); overImg.src = src(a.files.actual); stage.appendChild(over); slider.hidden = false; clip(); }
      else { base.src = src(a.files[m]); if (over.parentNode) stage.removeChild(over); slider.hidden = true; }
    };
    const clip = () => { over.style.width = slider.value + '%'; overImg.style.width = base.clientWidth + 'px'; };
    slider.oninput = clip;
    base.onload = () => { // small images are scaled up by an integer factor (pixelated) to stay readable
      base.style.width = base.naturalWidth * Math.max(1, Math.floor(320 / Math.max(1, base.naturalWidth))) + 'px';
      if (mode == 'slider') clip();
    };
    roles.forEach(r => { const b = el('button', '', r); b.dataset.m = r; b.onclick = () => set(r); modes.appendChild(b); });
    if (a.files.actual && a.files.reference) { const b = el('button', '', 'slider'); b.dataset.m = 'slider'; b.onclick = () => set('slider'); modes.appendChild(b); modes.appendChild(slider); }
    roles.forEach(r => { const l = el('a', 'metrics', r + ' file'); l.href = a.files[r]; l.target = '_blank'; modes.appendChild(l); });
    box.appendChild(modes); box.appendChild(stage); set(mode);
    return box;
  }

  function caseView(c) {
    const d = el('div', 'case');
    const head = el('div', 'head');
    head.appendChild(el('span', 'st ' + c.status, c.status));
    head.appendChild(el('span', 'name', c.name));
    head.appendChild(el('span', 'dur', fmt(c.duration)));
    d.appendChild(head);
    if (c.messages.length) d.appendChild(el('pre', '', c.messages.join('\n\n') + (c.location ? '\nat ' + c.location : '')));
    c.artifacts.forEach(a => d.appendChild(a.kind == 'image' ? imageViewer(a) : el('div', 'metrics', a.name)));
    return d;
  }

  function targetView(t, q, problemsOnly) {
    const det = el('details', 'target');
    const sum = el('summary');
    sum.appendChild(el('span', 'st ' + t.status, t.status));
    sum.appendChild(el('span', 'tid', t.id));
    const c = t.counts;
    sum.appendChild(el('span', 'layer', t.layer + ' · ' + c.passed + ' passed' + (c.failed + c.timeout + c.error ? ', ' + (c.failed + c.timeout + c.error) + ' failed' : '') + (c.skipped ? ', ' + c.skipped + ' skipped' : '') + (t.attempts > 1 ? ' · ' + t.attempts + ' attempts' : '')));
    sum.appendChild(el('span', 'dur', fmt(t.duration)));
    det.appendChild(sum);
    det.addEventListener('toggle', () => {
      if (!det.open || det.dataset.filled) return;
      det.dataset.filled = 1;
      const body = el('div', 'body');
      if (t.message) body.appendChild(el('div', 'msg', t.message));
      let cases = t.cases;
      if (problemsOnly) cases = cases.filter(x => PROBLEM.has(x.status));
      if (q) cases = cases.filter(x => x.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q));
      cases.forEach(x => body.appendChild(caseView(x)));
      if (t.log) {
        const ld = el('details'); ld.appendChild(el('summary', 'metrics', 'output log (' + t.log + ')'));
        const a = el('a', 'metrics', 'open full log'); a.href = t.log; a.target = '_blank'; ld.appendChild(a);
        ld.appendChild(el('pre', '', logs[t.log] || '(log not embedded)'));
        body.appendChild(ld);
      }
      det.appendChild(body);
    });
    if (PROBLEM.has(t.status)) det.open = true;
    return det;
  }

  function render() {
    const q = document.getElementById('q').value.trim().toLowerCase();
    const layer = layerSel.value, problemsOnly = document.getElementById('problemsOnly').checked;
    const list = document.getElementById('list'); list.textContent = '';
    const targets = run.targets.filter(t => shown.has(t.status) && (!layer || t.layer == layer) &&
      (!problemsOnly || PROBLEM.has(t.status)) &&
      (!q || t.id.toLowerCase().includes(q) || t.cases.some(c => c.name.toLowerCase().includes(q))));
    targets.forEach(t => list.appendChild(targetView(t, q, problemsOnly)));
    if (!targets.length) list.appendChild(el('div', 'empty', 'No targets match the filters.'));
  }
  ['q', 'layer', 'problemsOnly'].forEach(id => document.getElementById(id).addEventListener('input', render));
  render();
})();
</script>
</body>
</html>
'''
