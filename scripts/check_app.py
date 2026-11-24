"""Browser acceptance check for the P1 Workspace (pae-app).

    python scripts/check_app.py --output-dir results/runtime-p1-browser [--chrome PATH]

Starts the packaged server, drives Chromium with Playwright and checks:
  * the page loads without errors and the 3D canvas draws something
  * S1 designs a candidate; every drawn mirror/port coordinate and Fold mirror
    distance equals the engine scene within 1 nm (Gate of Roadmap P1)
  * editing an input marks the result stale and hides it from the drawings
  * failing scenarios show their reason, next step and rejection table
  * P3 glass scenarios: block card, hatched surface band, crossing record, TIR column,
    Fold surface marker at the air-gap distance, reflectors below the surface, 3D slab,
    turning the block off, and the shallow-guide region guidance
  * P4 coma correction: S1 corrected non-paraxial η ≥ 0.95, coefficient table and guidance
  * P3 non-paraxial check: η column and guidance on S1, beyond-guard study card on S3
  * P4 Lens Family on S3: Computed candidates in the table, Lens card, detail, lens drawn in 2D and the unfolded view
  * P4 Lens Family on S5: silicon source lens and silica target lens, both drawn in the unfolded view
  * P4 Family comparison card (S3 selects the lens Family) and the lens pose table
  * P3 q-tensor: S4 (non-coplanar) gives verified candidates, the q-tensor note and guidance,
    beam ellipses in the scene and 2D mirror positions equal to the scene vertices (1 nm)
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
    page.wait_for_selector('[data-result-status]', timeout=240000)  # S3 runs the P4 Lens Family (~20–60 s)
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
        np_cells = page.evaluate("""() => [...document.querySelectorAll('[data-nonparaxial]')].map(td => Number(td.dataset.nonparaxial))""")
        summary['S1_nonparaxial'] = np_cells
        check(np_cells and all(0 < v <= 1 for v in np_cells) and page.locator('[data-guidance="nonparaxial"]').count() == 1,
              f'S1 non-paraxial column/guidance: {np_cells}', failures)
        corrected = page.evaluate("""() => [...document.querySelectorAll('[data-corrected]')].map(td => Number(td.dataset.corrected))""")
        summary['S1_corrected'] = corrected
        check(corrected and all(v >= 0.95 for v in corrected) and page.locator('[data-freeform="Computed"]').count() == 1
              and page.locator('[data-guidance="freeform"]').count() == 1, f'S1 corrected surfaces (P4 gate): {corrected}', failures)
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

        load_scenario(page, 'S2b-1550')
        status = design(page)
        text = page.inner_text('[data-result-status]')
        summary['S2b-1550_status'] = status
        check(status == 'Computed' and 'Near-match' in text and page.locator('[data-guidance="exact_outside_guard"]').count() == 1,
              f'S2b near-match view: {status} {text[:120]}', failures)
        check(page.locator('.family.near_match').count() >= 3, 'S2b near-match candidates not labelled', failures)
        page.screenshot(path=str(out / 'p2_S2b-1550.png'))
        page.click('.tab[data-view="map"]')
        page.wait_for_timeout(300)
        gate = page.evaluate("""() => {
          const res = window.__paeStore.state.result;
          let worst = 0, count = 0;
          for (const c of res.candidates) {
            const mark = document.querySelector(`[data-kind="map-candidate"][data-id="${c.id}"]`);
            worst = Math.max(worst, Math.abs(Number(mark.dataset.aMm) - c.parameters_mm.a), Math.abs(Number(mark.dataset.cMm) - c.parameters_mm.c));
            count++;
          }
          return {worst, count, cells: document.querySelectorAll('[data-kind="map-cells"] rect').length};
        }""")
        summary['map_gate'] = gate
        check(gate['count'] >= 3 and gate['worst'] <= NM and gate['cells'] == 64 * 64, f'map view: {gate}', failures)
        page.screenshot(path=str(out / 'p2_S2b_map.png'))
        page.click('.tab[data-view="auto"]')

        load_scenario(page, 'S2a-1550')
        page.click('[data-action="add-keepout"]')
        page.wait_for_function("(window.__paeStore.state.doc.constraints?.keepouts_mm || []).length === 1", timeout=10000)
        status = design(page)
        summary['S2a-1550_keepout_status'] = status
        check(page.locator('[data-kind="keepout"]').count() >= 1, 'keep-out box not drawn in 2D', failures)
        hits = page.evaluate("""() => {
          const doc = window.__paeStore.state.doc, k = doc.constraints.keepouts_mm[0];
          const hit = (p, q) => { let lo = 0, hi = 1;
            for (let i = 0; i < 3; i++) { const d = q[i] - p[i];
              if (Math.abs(d) < 1e-15) { if (p[i] < k.min[i] || p[i] > k.max[i]) return false; continue; }
              let t0 = (k.min[i] - p[i]) / d, t1 = (k.max[i] - p[i]) / d; if (t0 > t1) [t0, t1] = [t1, t0];
              lo = Math.max(lo, t0); hi = Math.min(hi, t1); if (lo > hi) return false; }
            return true; };
          return window.__paeStore.state.result.candidates.map(c => c.scene.path.points_mm)
            .some(pts => pts.slice(1).some((q, i) => hit(pts[i], q)));
        }""")
        check(status in ('Computed', 'Fail') and not hits, f'keep-out violated or bad status: {status} {hits}', failures)
        page.screenshot(path=str(out / 'p2_S2a_keepout.png'))

        load_scenario(page, 'S2a-1550-glass')
        check(page.is_checked('[data-key="glass.enabled"]'), 'glass card not enabled for glass scenario', failures)
        check(page.locator('[data-kind="glass-surface"]').count() >= 1, 'glass surface not drawn in 2D', failures)
        status = design(page)
        summary['S2a-1550-glass_status'] = status
        check(status == 'Computed' and page.locator('[data-crossing="source"]').count() == 1, f'glass design view: {status}', failures)
        check(page.locator('[data-tir]').count() >= 2, 'TIR/coating column missing', failures)
        glass = page.evaluate("""() => {
          const c = window.__paeStore.selectedCandidate, out = {};
          const surface = document.querySelector('[data-kind="fold-surface"]');
          out.fold_surface_mm = surface ? Number(surface.getAttribute('data-distance-mm')) : null;
          out.gap_mm = window.__paeStore.state.result.crossing.ambient_length_mm;
          out.mirror_v = [...document.querySelectorAll('figure[data-view="xz"] [data-kind="mirror"]')].map(m => Number(m.getAttribute('data-v-mm')));
          out.surface_mm = [...document.querySelectorAll('figure[data-view="xz"] [data-kind="glass-surface"]')].map(m => Number(m.getAttribute('data-mm')));
          let slab = false;
          const v = window.__paeViewer; if (v && v.world) v.world.traverse(o => { if (o.userData && o.userData.kind === 'glass') slab = true; });
          out.slab = slab; out.webgl = Boolean(v && v.ok); out.candidate = c && c.id;
          return out; }""")
        summary['glass_view'] = glass
        check(glass['fold_surface_mm'] is not None and abs(glass['fold_surface_mm'] - glass['gap_mm']) < NM,
              f'Fold surface marker not at the air gap: {glass}', failures)
        check(glass['mirror_v'] and all(v < 0 for v in glass['mirror_v']) and glass['surface_mm'] == [0],
              f'reflectors not drawn below the glass surface: {glass}', failures)
        check(glass['slab'] or not glass['webgl'], '3D glass slab missing', failures)
        page.screenshot(path=str(out / 'p3_S2a-1550-glass.png'))
        page.uncheck('[data-key="glass.enabled"]')
        page.wait_for_function("!window.__paeStore.state.doc.medium_block && !window.__paeStore.state.doc.ports.target.medium", timeout=10000)
        check(page.locator('[data-kind="glass-surface"]').count() == 0, 'glass still drawn after turning it off', failures)

        load_scenario(page, 'S2b-1550-glass')
        status = design(page)
        summary['S2b-1550-glass_status'] = status
        check(status == 'Fail' and page.locator('[data-guidance="block_region"]').count() == 1,
              f'shallow IOX guidance missing: {status}', failures)
        page.screenshot(path=str(out / 'p3_S2b-1550-glass.png'))

        load_scenario(page, 'S4')
        status = design(page)
        summary['S4_status'] = status
        check(status == 'Computed' and page.locator('[data-model="qtensor"]').count() == 1
              and page.locator('[data-guidance="qtensor"]').count() == 1, f'S4 q-tensor view: {status}', failures)
        s4 = page.evaluate("""() => window.__paeStore.selectedCandidate.scene.beam.samples
          .every(s => s.ellipse && s.ellipse.major_um >= s.ellipse.minor_um)""")
        check(s4, 'S4 beam samples lack ellipses', failures)
        page.click('.tab[data-view="all"]')
        page.wait_for_timeout(200)
        gate = coordinate_gate(page)
        summary['S4_coordinate_gate_all'] = gate
        check(gate['count'] > 0 and gate['worst'] <= NM, f'S4 coordinate gate: {gate}', failures)
        page.screenshot(path=str(out / 'p3_S4_qtensor.png'))

        load_scenario(page, 'S3')
        status = design(page)
        text = page.inner_text('[data-result-status]')
        summary['S3_status'] = status
        check(status == 'Computed' and 'Lens Family' in text and page.locator('[data-guidance="port_divergence"]').count() >= 1,
              f'S3 lens family view: {status} {text[:80]}', failures)
        page.screenshot(path=str(out / 'p1_S3.png'))
        check(page.locator('[data-guard="source"].fail').count() == 1, 'S3 source guard not shown as Fail', failures)
        check(page.locator('[data-card="nonparaxial-study"] [data-study]').count() >= 1
              and page.locator('[data-guidance="nonparaxial_study"]').count() == 1, 'S3 non-paraxial study missing', failures)
        page.locator('[data-card="nonparaxial-study"]').screenshot(path=str(out / 'p3_S3_study.png'))
        rows = page.locator('[data-card="lens-review"] [data-lens-candidate]')
        check(rows.count() >= 1 and page.locator('[data-guidance="lens_review"]').count() == 1, 'S3 lens review card missing', failures)
        etas = [float(v) for v in page.eval_on_selector_all('[data-lens-eta]', 'els => els.map(e => e.dataset.lensEta)') if v]
        summary['S3_lens_review_eta'] = etas
        accepted = page.eval_on_selector_all('[data-lens-accepted]', 'els => els.map(e => e.dataset.lensAccepted)')
        check(etas and min(e for e, a in zip(etas, accepted) if a == 'true') >= 0.95
              and page.locator('tr[data-candidate]').count() == accepted.count('true'),
              f'S3 lens family η {etas} accepted {accepted}', failures)
        if rows.count():
            rows.first.click()
            page.wait_for_timeout(400)
            check(page.locator('[data-lens-detail]').count() == 1, 'S3 lens detail missing', failures)
            check(page.locator('[data-family-row="lens_two_reflector"][data-selected="true"]').count() == 1
                  and page.locator('[data-lens-pose] [data-decenter-1db]').count() >= 1, 'S3 family card or lens pose missing', failures)
            summary['S3_lens_decenter_1db_um'] = page.eval_on_selector_all('[data-decenter-1db]', 'els => els.map(e => e.getAttribute("data-decenter-1db"))')
            page.click('.tab[data-view="all"]')
            page.wait_for_timeout(300)
            check(page.locator('[data-kind="lens"]').count() >= 2 and page.locator('[data-kind="fold-lens"]').count() == 1,
                  'S3 lens not drawn in 2D / unfolded view', failures)
            page.screenshot(path=str(out / 'p4_S3_lens_family.png'))
            page.locator('[data-card="lens-review"]').screenshot(path=str(out / 'p4_S3_lens_card.png'))
            page.locator('[data-card="families"]').screenshot(path=str(out / 'p4_S3_families.png'))
            page.locator('[data-lens-detail]').screenshot(path=str(out / 'p4_S3_lens_detail.png'))
        load_scenario(page, 'S5')
        status = design(page)
        summary['S5_status'] = status
        materials = page.eval_on_selector_all('[data-lens-material]', 'els => els.map(e => e.dataset.lensMaterial)')
        summary['S5_lens_materials'] = materials
        check(status == 'Computed' and materials == ['Silicon', 'Fused silica']
              and page.locator('[data-kind="fold-lens"]').count() == 2, f'S5 lens family view: {status} {materials}', failures)
        page.screenshot(path=str(out / 'p4_S5_lens_family.png'))
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
