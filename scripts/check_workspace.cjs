const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync, spawn} = require('node:child_process');

async function main() {
  const dir = process.argv[2];
  const baselineDir = process.argv[3];
  assert(dir && baselineDir, 'provide new output directory and fresh M5-A evidence directory');
  const head = execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim();
  const baselineEvidence = JSON.parse(fs.readFileSync(path.join(baselineDir, 'provenance.json')));
  assert.equal(baselineEvidence.evaluated_checkout_sha, head);
  assert.equal(baselineEvidence.status, 'Pass');
  fs.mkdirSync(dir);
  const server = spawn('python', ['-m','photonic_architecture_explorer.workspace','--port','0'],
                       {stdio: ['ignore', 'pipe', 'inherit']});
  let browser;
  try {
    const address = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('workspace startup timeout')), 10000);
      server.once('error', reject);
      server.once('exit', code => reject(new Error('workspace exited ' + code)));
      server.stdout.on('data', chunk => {
        const match = String(chunk).match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) {
          clearTimeout(timeout);
          resolve(match[0]);
        }
      });
    });
    browser = await chromium.launch();
    const errors = [];
    const page = await browser.newPage({viewport: {width: 1440, height: 1050}, acceptDownloads: true});
    page.on('pageerror', error => errors.push(error.message));
    const output = page.locator('#design-output');
    const frame = page.frameLocator('#design-review');
    const byName = name => page.locator('input[name="' + name + '"]');
    const edit = (name, value) => byName(name).fill(value);
    const result = () => frame.locator('#design-result').evaluate(el => JSON.parse(el.textContent));
    const design = async status => {
      await Promise.all([page.waitForEvent('framenavigated', {
                           predicate: current => current === page.mainFrame() && new URL(current.url()).pathname === '/design'
                         }), page.getByRole('button', {name: 'Design', exact: true}).click()]);
      await frame.locator('#design-result').waitFor({state: 'attached'});
      assert.equal(await output.getAttribute('data-status'), status);
      const data = await result();
      assert.equal(data.status, status);
      return data;
    };
    const assertClean = async () => {
      assert.equal(await output.isVisible(), false);
      assert.equal(await page.locator('#pending').isVisible(), true);
      assert.equal(await page.getByRole('button', {name: 'HTML 저장'}).isVisible(), false);
      assert.equal(await page.locator('#design-review').isVisible(), false);
    };
    const verifyModeMatch = async (view, data, candidateId) => {
      const active = view.locator('[data-candidate]:visible');
      assert.equal(await active.getAttribute('data-candidate'), candidateId);
      const candidate = data.candidates.find(item => item.id === candidateId);
      const mode = active.locator('[data-mode-match]');
      assert.equal(await mode.getAttribute('data-mode-match'), candidateId);
      assert.equal(await mode.getAttribute('data-input-sha'), data.input_sha256);
      for (const port of ['source', 'target']) {
        const plane = data.input_snapshot[port].reference_plane.value;
        assert.deepEqual(plane, candidate.prescription[port].reference_plane.value);
        assert.equal(await mode.getAttribute('data-' + port + '-plane'), plane.id);
      }
      const eta = candidate.evaluation.gaussian_mode_matching.normalized_mode_overlap;
      assert.equal(Number(await mode.getAttribute('data-mode-eta')), eta);
      assert.equal(Number(await active.locator('[data-overlap-value]:visible').innerText()), eta);
      if (!(await mode.evaluate(node => node.open))) await mode.locator('summary').click();
      assert.equal(await mode.locator('svg:visible').count(), 6);
      assert.match(await mode.locator('[data-mismatch-loss]').innerText(), / dB$/);
    };
    const verifySensitivity = async (view, data, candidateId) => {
      const active = view.locator('[data-candidate]:visible');
      const panel = active.locator('[data-sensitivity]');
      const diagnostic = data.candidate_sensitivity;
      assert.equal(diagnostic.status, 'Approximate');
      assert.equal(diagnostic.input_sha256, data.input_sha256);
      assert.deepEqual(diagnostic.target_reference_plane, data.input_snapshot.target.reference_plane.value);
      assert.equal(diagnostic.recommended_candidate_id, data.selected_candidate_id);
      assert.deepEqual(diagnostic.candidates.map(row => row.candidate_id), data.candidates.map(row => row.id));
      assert.equal(await panel.getAttribute('data-sensitivity'), candidateId);
      assert.equal(await panel.getAttribute('data-input-sha'), data.input_sha256);
      assert.equal(await panel.getAttribute('data-target-plane'), diagnostic.target_reference_plane.id);
      assert.equal(await panel.locator('th[aria-current]').getAttribute('data-sensitivity-candidate'), candidateId);
      if (!(await panel.evaluate(node => node.open))) await panel.locator('summary').click();
      assert.equal(await panel.locator('tbody tr:visible').count(), 9);
      for (const column of diagnostic.candidates) {
        const row = await panel.locator('[data-sensitivity-scenario="offset_m-t-plus"]')
          .locator('[data-sensitivity-cell="' + column.candidate_id + '"]').innerText();
        const match = row.match(/^(\d+\.\d+) \(([+-]?\d+\.\d+)\)$/);
        assert(match, 'expected rendered loss and delta values');
        const sample = column.samples['offset_m-t-plus'];
        assert(Math.abs(Number(match[1]) - sample.mode_mismatch_loss_db) <= 0.000051);
        assert(Math.abs(Number(match[2]) - sample.delta_loss_db) <= 0.000051);
      }
    };
    const download = async format => {
      const [item] = await Promise.all([page.waitForEvent('download'),
                                       page.locator('[data-export="' + format + '"]').click()]);
      assert.equal(item.suggestedFilename(), 'design.' + format);
      const dest = path.join(dir, 'design.' + format);
      await item.saveAs(dest);
      assert.equal(await item.failure(), null);
      return dest;
    };

    await page.goto(address);
    assert.equal(await page.locator('#design-review').count(), 0);
    const nominal = await design('Computed');
    const {candidate_sensitivity: sensitivity, ...coreResult} = nominal;
    assert.deepEqual(coreResult, JSON.parse(fs.readFileSync(path.join(baselineDir, 'design.json'))));
    await verifySensitivity(frame, nominal, nominal.selected_candidate_id);
    await edit('target_position_m_2', '2.2');
    await assertClean();
    const revised = await design('Computed');
    assert.notEqual(revised.input_sha256, nominal.input_sha256);
    assert.equal(revised.input_snapshot.target.position_m.value[2], 0.0022);
    assert.deepEqual(revised.input_snapshot.source, nominal.input_snapshot.source);
    assert.deepEqual(revised.input_snapshot.target.reference_plane.value.origin_m, revised.input_snapshot.target.position_m.value);
    for (const candidate of revised.candidates) {
      assert.equal(candidate.classification, 'Conceptual Geometry');
      assert.equal(candidate.evaluation.package_feasibility.status, 'Uncomputed');
      for (const name of ['source', 'target']) {
        assert.deepEqual(candidate.prescription[name], revised.input_snapshot[name]);
      }
    }
    assert.equal(revised.physical_losses.total_coupling, null);
    const alternativeId = revised.candidates[1].id;
    await frame.locator('#candidate-select').selectOption(alternativeId);
    await verifyModeMatch(frame, revised, alternativeId);
    await verifySensitivity(frame, revised, alternativeId);
    await page.screenshot({path: path.join(dir, 'workspace-desktop.png'), fullPage: true});

    const html = await download('html');
    const json = await download('json');
    const exported = {...revised, viewed_candidate_id: alternativeId};
    assert.deepEqual(JSON.parse(fs.readFileSync(json)), exported);
    const standalone = await browser.newPage();
    await standalone.route('http**://**/*', route => route.abort());
    await standalone.goto('file://' + path.resolve(html));
    assert.deepEqual(await standalone.locator('#design-result').evaluate(el => JSON.parse(el.textContent)), exported);
    await verifyModeMatch(standalone, exported, alternativeId);
    await verifySensitivity(standalone, exported, alternativeId);
    await standalone.close();

    await edit('source_wavefront_curvature_ts_per_m_0', '');
    await edit('source_wavefront_curvature_ts_per_m_1', '');
    await assertClean();
    let rejected = await design('Uncomputed');
    assert.equal(rejected.input_snapshot.source.wavefront_curvature_ts_per_m.value, null);
    assert.match(rejected.reason, /no waist default/);
    assert.equal(await frame.locator('[data-overlap-value]').count(), 0);
    assert.equal(await frame.locator('[data-mode-match]').count(), 0);
    assert.equal(rejected.candidate_sensitivity.status, 'Uncomputed');
    assert.equal(await frame.locator('[data-sensitivity-cell]').count(), 0);
    await edit('source_wavefront_curvature_ts_per_m_0', '0');
    await edit('source_wavefront_curvature_ts_per_m_1', '0');
    assert.equal((await design('Computed')).input_sha256, revised.input_sha256);

    await edit('source_propagation_direction_0', '0');
    rejected = await design('Fail');
    assert.match(rejected.reason, /unit vector/);
    assert.equal(await frame.locator('[data-overlap-value]').count(), 0);
    assert.equal(await frame.locator('[data-mode-match]').count(), 0);
    assert.equal(rejected.candidate_sensitivity.status, 'Uncomputed');
    assert.equal(await frame.locator('[data-sensitivity-cell]').count(), 0);
    await edit('source_propagation_direction_0', '1');
    await edit('source_mfd_ts_m_0', '2');
    await edit('source_mfd_ts_m_1', '2');
    rejected = await design('Fail');
    assert.match(rejected.reason, /divergence/);
    assert.equal(await frame.locator('[data-overlap-value]').count(), 0);
    assert.equal(await frame.locator('[data-mode-match]').count(), 0);
    assert.equal(rejected.candidate_sensitivity.status, 'Uncomputed');
    assert.equal(await frame.locator('[data-sensitivity-cell]').count(), 0);
    await edit('source_mfd_ts_m_0', '16');
    await edit('source_mfd_ts_m_1', '24');
    await design('Computed');

    await page.setViewportSize({width: 393, height: 852});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert(await frame.locator('html').evaluate(el => el.scrollWidth <= el.clientWidth));
    const alternatives = frame.locator('#candidate-select option');
    assert((await alternatives.count()) >= 2);
    await frame.locator('#candidate-select').selectOption({index: 1});
    assert.equal(await frame.locator('[data-candidate]:visible').count(), 1);
    await frame.locator('#projection-select').selectOption('XY');
    assert.equal(await frame.locator('[data-projection="XY"]:visible').count(), 1);
    const mobileData = await result();
    const mobileCandidate = await frame.locator('#candidate-select').inputValue();
    await verifyModeMatch(frame, mobileData, mobileCandidate);
    await verifySensitivity(frame, mobileData, mobileCandidate);
    assert(await frame.locator('html').evaluate(el => el.scrollWidth <= el.clientWidth));
    await page.screenshot({path: path.join(dir, 'workspace-mobile.png'), fullPage: true});

    await page.getByRole('link', {name: '새 입력'}).click();
    assert.equal(await byName('wavelength_m_0').inputValue(), '');
    assert.equal(await byName('target_position_m_2').inputValue(), '');
    assert.equal(await byName('source_wavefront_curvature_ts_per_m_0').inputValue(), '');
    assert.equal(await page.locator('#design-review').count(), 0);
    await page.locator('select[name="source_mode"]').selectOption('q');
    assert.equal(await byName('source_complex_q_ts_m_0').isVisible(), true);
    assert.equal(await byName('source_wavefront_curvature_ts_per_m_0').isVisible(), false);
    assert.deepEqual(errors, []);

    const evidence = {status: 'Pass', evaluated_checkout_sha: head, browser: await browser.version(),
      nominal_sensitivity: sensitivity.candidates.map(entry => ({
        candidate_id: entry.candidate_id,
        delta_db: Object.fromEntries(Object.entries(entry.samples).map(([id, value]) => [id, value.delta_loss_db]))
      })),
      checks: ['fresh M5-A synthetic exact match', 'edited fixed Port and reference plane', 'immediate stale result and export hiding',
               'missing phase and recovery', 'invalid unit vector and high divergence', 'Uncomputed package and total coupling',
               'standalone HTML and JSON identical data and viewed candidate', 'Mode Match candidate/planes/SHA/overlap agreement', 'sensitivity candidate order, values and export agreement', 'desktop and 393px mobile', 'blank input and complex q controls']};
    fs.writeFileSync(path.join(dir, 'browser.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence));
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
}

main().catch(error => {console.error(error); process.exit(1);});
