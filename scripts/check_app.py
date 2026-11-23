"""Browser acceptance check for the P1 Workspace (pae-app).

    python scripts/check_app.py --output-dir results/runtime-p1-browser [--chrome PATH]

Starts the packaged server, drives Chromium with Playwright and checks:
  * the page loads without errors and the 3D canvas draws something
  * S1 designs a candidate; every drawn mirror/port coordinate and Fold mirror
    distance equals the engine scene within 1 nm (Gate of Roadmap P1)
  * editing an input marks the result stale and hides it from the drawings
  * failing scenarios show their reason, next step and rejection table
  * Design Document export round-trips
  * without WebGL the 2D drawings still work
Screenshots and a JSON summary go to the output directory.
"""

import argparse
import json
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from playwright.sync_api import sync_playwright  # noqa: E402

from photonic_architecture_explorer.app import make_server  # noqa: E402

NM = 1e-6  # mm
SWIFTSHADER = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']


def check(condition, message, failures):
    if not condition:
        failures.append(message)
    return condition


def coordinate_gate(page):
    """Compare every drawn marker with the engine scene fetched for the same document."""
    return page.evaluate("""async () => {
      const doc = window.__paeStore.state.doc;
      const res = await (await fetch('api/design', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(doc)})).json();
      const cand = res.candidates.find(c => c.id === window.__paeStore.state.selected) || res.candidates[0];
      const axes = {xy: [0, 1], xz: [0, 2], yz: [1, 2]};
      let worst = 0, count = 0;
      for (const fig of document.querySelectorAll('figure[data-view]')) {
        const view = fig.dataset.view;
        if (view === 'fold') {
          let travelled = 0;
          cand.scene.path.segments.forEach((s, j) => {
            travelled += s.length_mm;
            const line = fig.querySelector(`[data-kind="fold-mirror"][data-id="M${j + 1}"]`);
            if (line) { worst = Math.max(worst, Math.abs(Number(line.dataset.distanceMm) - travelled)); count++; }
          });
          continue;
        }
        const [a, b] = axes[view];
        for (const m of cand.scene.mirrors) {
          const mark = fig.querySelector(`[data-kind="mirror"][data-id="${m.id}"]`);
          worst = Math.max(worst, Math.abs(Number(mark.dataset.uMm) - m.vertex_mm[a]), Math.abs(Number(mark.dataset.vMm) - m.vertex_mm[b]));
          count++;
        }
        for (const name of ['source', 'target']) {
          const mark = fig.querySelector(`[data-kind="port"][data-id="${name}"]`);
          const p = doc.ports[name].position_mm;
          worst = Math.max(worst, Math.abs(Number(mark.dataset.uMm) - p[a]), Math.abs(Number(mark.dataset.vMm) - p[b]));
          count++;
        }
      }
      return {worst, count};
    }""")


def canvas_ink(page):
    return page.evaluate("""() => {
      const gl = document.querySelector('.viewer canvas');
      if (!gl) return -1;
      const c = document.createElement('canvas'); c.width = gl.width; c.height = gl.height;
      const ctx = c.getContext('2d'); ctx.drawImage(gl, 0, 0);
      const d = ctx.getImageData(0, 0, c.width, c.height).data;
      let ink = 0; for (let i = 0; i < d.length; i += 16) if (d[i] < 200 || d[i + 1] < 200 || d[i + 2] < 200) ink++;
      return ink;
    }""")


def design(page):
    page.click('#design')
    page.wait_for_selector('[data-result-status]', timeout=60000)
    page.wait_for_timeout(500)
    return page.get_attribute('[data-result-status]', 'data-result-status')


def load_scenario(page, scenario):
    page.select_option('#scenario', scenario)
    page.wait_for_function(f"window.__paeStore.state.doc.scenario === '{scenario}' && window.__paeStore.state.preview", timeout=20000)
    page.wait_for_timeout(300)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results/runtime-p1-browser')
    parser.add_argument('--chrome', default=None, help='Chromium/Chrome executable (default: Playwright Chromium)')
    parser.add_argument('--channel', default=None, help='Playwright browser channel, e.g. msedge or chrome')
    parser.add_argument('--url', default=None, help='Check an already running Workspace (e.g. the Windows package)')
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    server = None
    if args.url:
        url = args.url if args.url.endswith('/') else args.url + '/'
    else:
        server = make_server(0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_address[1]}/'
    failures, summary = [], {}
    with sync_playwright() as pw:
        launch = {'args': SWIFTSHADER, **({'executable_path': args.chrome} if args.chrome else {}),
                  **({'channel': args.channel} if args.channel else {})}
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1600, 'height': 1000}, accept_downloads=True)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_selector("body[data-ready='1']", timeout=30000)
        page.wait_for_function('window.__paeStore.state.preview', timeout=20000)
        page.wait_for_timeout(800)
        summary['canvas_ink_initial'] = canvas_ink(page)
        check(summary['canvas_ink_initial'] > 50, '3D canvas did not draw', failures)

        status = design(page)
        summary['S1_status'] = status
        check(status == 'Computed', f'S1 status {status}', failures)
        check(page.locator('[data-candidate]').count() >= 1, 'S1 candidate table empty', failures)
        page.screenshot(path=str(out / 'p1_S1_auto.png'))
        for view in ('all', 'xz', 'fold'):
            page.click(f'.tab[data-view="{view}"]')
            page.wait_for_timeout(200)
            gate = coordinate_gate(page)
            summary[f'coordinate_gate_{view}'] = gate
            check(gate['count'] > 0 and gate['worst'] <= NM, f'coordinate gate {view}: {gate}', failures)
            page.screenshot(path=str(out / f'p1_S1_{view}.png'))
        page.click('.tab[data-view="auto"]')

        with page.expect_download() as info:
            page.click('text=입력 JSON')
        exported = json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
        current = page.evaluate('window.__paeStore.state.doc')
        check(exported == current, 'exported Design Document differs from the editor state', failures)

        page.fill('[data-key="target.position_mm.2"]', '2.5')
        page.dispatch_event('[data-key="target.position_mm.2"]', 'change')
        page.wait_for_selector('.card.stale', timeout=10000)
        check(page.locator('[data-kind="mirror"]').count() == 0, 'stale result still drawn', failures)
        summary['stale_hidden'] = True
        page.screenshot(path=str(out / 'p1_stale.png'))

        for scenario, reason in (('S2b-1550', '고정 Exact-q'), ('S3', '발산각')):
            load_scenario(page, scenario)
            status = design(page)
            text = page.inner_text('[data-result-status]')
            summary[f'{scenario}_status'] = status
            check(status == 'Fail' and reason in text and '다음 단계' in text, f'{scenario} failure view: {status} {text[:80]}', failures)
            page.screenshot(path=str(out / f'p1_{scenario}.png'))
        check(page.locator('[data-guard="source"].fail').count() == 1, 'S3 source guard not shown as Fail', failures)
        check(not errors, f'page errors: {errors}', failures)
        summary['page_errors'] = errors

        no_gl = browser.new_context(viewport={'width': 1400, 'height': 900}).new_page()
        no_gl.add_init_script("""HTMLCanvasElement.prototype.getContext = new Proxy(HTMLCanvasElement.prototype.getContext,
          {apply(t, self, a) { return /webgl/.test(a[0]) ? null : Reflect.apply(t, self, a); }});""")
        no_gl.goto(url)
        no_gl.wait_for_selector("body[data-ready='1']", timeout=30000)
        no_gl.wait_for_function('window.__paeStore.state.preview', timeout=20000)
        check(no_gl.locator('.fallback').count() == 1, 'WebGL fallback message missing', failures)
        status = design(no_gl)
        check(status == 'Computed' and no_gl.locator('[data-kind="mirror"]').count() > 0, 'no-WebGL 2D drawings missing', failures)
        no_gl.screenshot(path=str(out / 'p1_no_webgl.png'))
        browser.close()
    if server:
        server.shutdown()
    summary['browser'] = args.channel or args.chrome or 'playwright-chromium'
    summary['status'] = 'Pass' if not failures else 'Fail'
    summary['failures'] = failures
    (out / 'p1_browser.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
