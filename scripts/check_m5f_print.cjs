const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');

async function checkCase(browser, root, test) {
  const dir = path.join(root, test.id);
  const payload = JSON.parse(fs.readFileSync(path.join(dir, 'design.json')));
  assert.equal(payload.status, test.status);
  assert.equal(payload.input_sha256, test.input_sha256);
  const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
  try {
    await page.route('http**://**/*', route => route.abort());
    await page.goto(pathToFileURL(path.resolve(dir, 'design.html')).href);
    const embedded = await page.locator('#design-result').evaluate(el => JSON.parse(el.textContent));
    assert.deepEqual(embedded, payload);

    const visibleValues = [];
    if (test.status === 'Computed') {
      const id = test.recommended;
      assert.equal(await page.locator('#candidate-select').inputValue(), id);
      await page.locator('#review-toggle').click();
      const selected = page.locator('[data-review-candidate]:visible');
      assert.equal(await selected.getAttribute('data-review-candidate'), id);
      assert.equal(await selected.getAttribute('data-input-sha'), payload.input_sha256);
      const record = payload.candidate_review.candidates[id];
      assert.equal(record.recommendation_role, 'short_path');
      assert.equal(payload.candidates[0].recommendation_role, record.recommendation_role);
      const role = await selected.locator('[data-review-concept]').innerText();
      assert.equal(role, '최단 광경로');
      const overlap = 'Overlap ' + (record.overlap * 100).toFixed(6) + '%';
      assert((await selected.locator('[data-review-nominal]').innerText()).startsWith(overlap));
      const length = 'Path ' + (record.total_path_m * 1000).toFixed(3) + ' mm';
      assert.equal(await selected.locator('[data-review-length]').innerText(), length);
      visibleValues.push('Candidate Review · ' + id, role, overlap, length);
      for (const port of ['source', 'target']) {
        const fixed = payload.input_snapshot[port].reference_plane.value;
        assert.deepEqual(record.ports[port].reference_plane, fixed);
        const row = await selected.locator('[data-review-port="' + port + '"]').innerText();
        assert(row.includes(fixed.id));
        visibleValues.push(fixed.id);
      }
      for (const row of payload.candidate_review.scenarios) {
        const entry = record.sensitivity_samples[row.id];
        const cell = selected.locator('[data-review-scenario="' + row.id + '"] td');
        const absolute = await cell.nth(0).innerText();
        const delta = await cell.nth(1).innerText();
        assert(Math.abs(Number(absolute) - entry.mode_mismatch_loss_db) < 0.000051);
        assert(Math.abs(Number(delta) - entry.delta_loss_db) < 0.000051);
        visibleValues.push(row.label + ' ' + absolute + ' ' + delta);
      }
      await page.locator('#review-toggle').click();
    } else {
      assert.equal(await page.locator('#candidate-review,[data-review-candidate]').count(), 0);
      assert.equal(await page.locator('[data-design-failure]').innerText(), payload.reason);
      assert((await page.locator('#rejected-design').innerText()).includes('Overlap: Uncomputed'));
      assert.equal(await page.locator('[data-sensitivity-uncomputed]').count(), 1);
      visibleValues.push(payload.reason, 'Overlap: Uncomputed', 'Target 기준면 민감도 · Uncomputed');
    }

    await page.emulateMedia({media: 'print'});
    const file = path.join(dir, 'design.pdf');
    await page.pdf({path: file, preferCSSPageSize: true, printBackground: true});
    const metadata = execFileSync('pdfinfo', [file], {encoding: 'utf8'});
    assert.match(metadata, /^Pages:\s+1\s*$/m);
    const paper = metadata.match(/^Page size:\s+([\d.]+) x ([\d.]+) pts/m);
    assert(paper && Math.abs(Number(paper[1]) - 595.28) < 2 &&
           Math.abs(Number(paper[2]) - 841.89) < 2, metadata);
    const printed = execFileSync('pdftotext', ['-layout', file, '-'], {encoding: 'utf8'}).replace(/\s+/g, ' ');
    for (const value of [payload.input_sha256, ...visibleValues]) {
      assert(printed.includes(value), 'missing ' + value + ' in print text: ' + printed);
    }
    assert.equal((printed.match(/Candidate Review ·/g) || []).length, test.status === 'Computed' ? 1 : 0);
    if (test.status === 'Computed') {
      assert(printed.includes('실제 부품 배치 공차 및 Off-vertex field handoff: Uncomputed'));
      assert(printed.includes('Package Yield Uncomputed'));
      assert(printed.includes('Total Coupling Uncomputed'));
    } else {
      assert(printed.includes('Total Coupling: Uncomputed'));
    }
    return {id: test.id, pages: 1, paper: 'A4', status: test.status, input_sha256: test.input_sha256};
  } finally {
    await page.close();
  }
}

async function main() {
  const root = process.argv[2];
  assert(root, 'provide the M5-F evidence directory');
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'acceptance.json')));
  assert.equal(manifest.head, execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim());
  assert.equal(manifest.cases.length, 3);
  const browser = await chromium.launch();
  try {
    const cases = [];
    for (const test of manifest.cases) cases.push(await checkCase(browser, root, test));
    const evidence = {status: 'Pass', head: manifest.head, browser: browser.version(), cases};
    fs.writeFileSync(path.join(root, 'print-evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exit(1); });
