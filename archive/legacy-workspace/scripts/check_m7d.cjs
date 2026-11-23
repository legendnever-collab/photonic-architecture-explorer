// Real installed worker, late-response control, responsive UI and export/A4 acceptance.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {spawn, execFileSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');

async function main() {
  const dir = path.resolve(process.argv[2]);
  fs.mkdirSync(dir);
  const serverCode = `
import signal,sys,os
from pathlib import Path
from photonic_architecture_explorer.workspace import Workspace
from photonic_architecture_explorer.workflow_jobs import JobManager
from photonic_architecture_explorer.inspector import make_server
import photonic_architecture_explorer as module
if os.environ.get('PAE_EXPECT_ROOT'):
 assert Path(module.__file__).resolve().is_relative_to(Path(os.environ['PAE_EXPECT_ROOT']).resolve())
def stop(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
workspace=Workspace()
workspace.jobs=JobManager(root=Path(sys.argv[1])/'jobs')
with make_server((),0,workspace=workspace) as server:
 print('http://127.0.0.1:'+str(server.server_port),flush=True)
 try: server.serve_forever()
 except KeyboardInterrupt: pass
`;
  const server = spawn(process.env.PAE_PYTHON || 'python', ['-u','-c',serverCode,dir], {stdio:['ignore','pipe','inherit']});
  let browser;
  try {
    const address = await new Promise((resolve,reject) => {
      const timer=setTimeout(()=>reject(new Error('Server startup timeout')),10000);
      server.once('error',reject);
      server.once('exit',code=>reject(new Error('Server exited '+code)));
      server.stdout.on('data',data=>{
        const match=String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
        if(match){clearTimeout(timer);resolve(match[0]);}
      });
    });
    browser=await chromium.launch(process.env.PAE_CHROMIUM ? {executablePath:process.env.PAE_CHROMIUM} : {});
    const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
    let page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.setDefaultTimeout(10000);
    const frame=()=>page.frameLocator('#design-review');
    const result=()=>frame().locator('#design-result').evaluate(e=>JSON.parse(e.textContent));
    const design=async()=>{
      await Promise.all([page.waitForEvent('framenavigated', {predicate:f=>f===page.mainFrame() &&
        new URL(f.url()).pathname==='/design'}),page.getByRole('button',{name:'Design',exact:true}).click()]);
    };
    const identity=()=>page.locator('#workflow-job').evaluate(e=>JSON.parse(e.textContent));
    const urlFor=id=>address+'/jobs/status?'+new URLSearchParams(id);
    const status=async id=>{
      const response=await page.request.get(urlFor(id));
      assert.equal(response.status(),200);
      return response.json();
    };
    const hidden=async()=>{
      assert.equal(await page.locator('#design-output').isVisible(),false);
      assert.equal(await page.locator('[data-export]:visible').count(),0);
    };
    const openReference=async()=>{
      const [referencePage]=await Promise.all([
        page.context().waitForEvent('page'),
        page.getByRole('link',{name:'SMF–Glass Mode Reference'}).click(),
      ]);
      referencePage.on('pageerror',e=>errors.push(e.message));
      referencePage.setDefaultTimeout(10000);
      await referencePage.setViewportSize(page.viewportSize());
      await referencePage.waitForURL(url=>url.searchParams.get('entry')==='mode-references');
      return referencePage;
    };
    await page.goto(address);
    await design();
    const exact=await result();
    assert.equal(exact.selected_candidate_id,'G009-B1');
    assert.equal(await page.locator('#workflow-job').count(),0);
    const exactHTML=await page.locator('#design-review').getAttribute('srcdoc');

    const openR6 = async () => {
      await page.goto(address);
      await page.getByRole('tab', {name:'Tutorial / How It Works'}).click();
      await page.frameLocator('#guide-frame').getByRole('link', {name:'이 두 Port로 설계'}).click();
      await page.waitForURL(url => url.searchParams.get('entry') === 'smf-glass-1310');
      assert.equal(await page.locator('[name="wavelength_m_0"]').inputValue(), '1310');
      assert.equal(await page.locator('#workflow-job, #design-review').count(), 0);
    };

    // Start an actual eligible job and cancel it from the Desktop UI.
    await openR6();
    await design();
    const cancelled=await identity();
    await hidden();
    await page.waitForFunction(()=>/평가 [1-9]/.test(document.querySelector('#job-status').textContent),null,{timeout:30000});
    const pingStart=Date.now();
    assert.equal((await page.request.get(address)).status(),200);
    const pingMs=Date.now()-pingStart;
    assert(pingMs<5000,'Background worker blocked the HTTP server');
    await page.getByRole('button',{name:'취소',exact:true}).click();
    await hidden();
    await expectTerminal(cancelled,'Cancelled');

    // Deliberately hold a status reply, edit on Mobile, then deliver an old-result control.
    await page.setViewportSize({width:393,height:852});
    await openR6();
    let release,heldResolve;
    const held=new Promise(r=>heldResolve=r);
    const gate=new Promise(r=>release=r);
    let trapped=false;
    await page.route('**/jobs/status?**',async route=>{
      if(trapped) return route.continue();
      trapped=true;
      const response=await route.fetch();
      const data=await response.json();
      heldResolve();
      await gate;
      // Transport-only stale-reply control. Never used as performance evidence.
      await route.fulfill({json:{...data,state:'Succeeded',result_status:'Computed',report_html:exactHTML}});
    });
    await design();
    const edited=await identity();
    await held;
    await page.locator('input[name="target_position_m_2"]').fill('2.001');
    release();
    await page.waitForTimeout(700);
    await hidden();
    assert.match(await page.locator('#job-status').innerText(),/입력이 변경/);
    await expectTerminal(edited,'Cancelled');
    await page.unroute('**/jobs/status?**');

    // Start the full retry through the packaged read-only reference and explicit Proxy link.
    const referencePage=await openReference();
    const comparison=referencePage.locator('#comparison-1550');
    assert.equal(await comparison.locator('polyline').count(),6);
    assert(await comparison.getByRole('link',{name:/Fig. 5\(b\) measured intensity/}).isVisible());
    assert.equal(await referencePage.locator('form, #design-review, #workflow-job').count(),0);
    await referencePage.screenshot({path:path.join(dir,'reference-1550.png'),fullPage:true});
    await referencePage.getByRole('link',{name:'1550 nm SMF–Glass 개념 Proxy 열기'}).click();
    assert.equal(await referencePage.locator('input[name="wavelength_m_0"]').inputValue(),'1550');
    assert.equal(await referencePage.locator('#design-review, #workflow-job').count(),0);
    await page.close();
    page=referencePage;
    await design();
    const completed=await identity();
    assert.notEqual(completed.job_id,cancelled.job_id);
    assert.notEqual(completed.revision,edited.revision);
    assert.notEqual(completed.input_sha256,cancelled.input_sha256);
    await hidden();
    let terminalObserved=false;
    const monitor=async()=>{
      let reportAt=0;
      while(!terminalObserved){
        const current=await status(completed);
        if(['Failed','TimedOut','Cancelled'].includes(current.state))
          throw new Error('Worker did not publish a result: '+JSON.stringify(current));
        if(Date.now()-reportAt>10000){
          console.log(JSON.stringify({job_id:completed.job_id,state:current.state,progress:current.progress}));
          reportAt=Date.now();
        }
        await page.waitForTimeout(500);
      }
    };
    try {
      await Promise.race([frame().locator('#design-result').waitFor({state:'attached',timeout:650000}),monitor()]);
    } finally { terminalObserved=true; }
    const near=await result();
    assert.equal(near.selected_candidate_id,'G036-NM');
    assert.equal(near.workflow.job_id,completed.job_id);
    assert.equal(near.input_sha256,completed.input_sha256);
    assert.equal(near.workflow.state,'Succeeded');
    assert.equal(near.workflow.near_match.adapter_calls,124160);
    assert.equal(near.candidates.length,1);
    const candidate=near.candidates[0];
    assert(Math.abs(candidate.evaluation.gaussian_mode_matching.normalized_mode_overlap-0.9999366495865395)<1e-10);
    for(const name of ['source','target']) assert.deepEqual(candidate.prescription[name],near.input_snapshot[name]);
    for(const key of ['actual_applicability','physical_losses','fabrication_yield','patentability'])
      assert.equal(near[key].status,'Uncomputed');
    assert.equal(candidate.independent_validation.status,'Pass');
    const reference=JSON.parse(fs.readFileSync('results/m7b_near_match.json'));
    for(let i=0;i<36;i++){
      const a=near.workflow.near_match.geometries[i],b=reference.geometries[i];
      for(const key of ['geometry_id','calls','counts','termination']) assert.deepEqual(a[key],b[key]);
      if(a.best) assert(Math.abs(a.best.overlap-b.best_overlap)<=1e-10);
      else assert.equal(b.best_overlap,null);
    }
    const protectedFiles=['design.py','external.py','gaussian.py','geometry.py','solver.py'];
    for(const [file,digest] of Object.entries(reference.manifest.source_sha256)){
      if(protectedFiles.includes(path.basename(file)))
        assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),digest);
    }
    assert(await frame().locator('[data-candidate]:visible [data-near-match]').isVisible());
    await page.screenshot({path:path.join(dir,'mobile-completed.png'),fullPage:true});
    await page.setViewportSize({width:1440,height:1050});
    await page.screenshot({path:path.join(dir,'desktop-completed.png'),fullPage:true});
    const exportFile=async (format, stem='design')=>{
      const downloadPromise=page.waitForEvent('download');
      await page.locator('[data-export="'+format+'"]').click();
      const download=await downloadPromise;
      const target=path.join(dir,stem+'.'+format);
      await download.saveAs(target);
      return target;
    };
    const jsonFile=await exportFile('json');
    const htmlFile=await exportFile('html');
    const exported=JSON.parse(fs.readFileSync(jsonFile));
    assert.equal(exported.viewed_candidate_id,'G036-NM');
    delete exported.viewed_candidate_id;
    assert.deepEqual(exported,near);
    const offline=await browser.newPage();
    await offline.goto(pathToFileURL(htmlFile).href);
    const embedded=await offline.locator('#design-result').evaluate(e=>JSON.parse(e.textContent));
    delete embedded.viewed_candidate_id;
    assert.deepEqual(embedded,near);
    await offline.pdf({path:path.join(dir,'review.pdf'),format:'A4',preferCSSPageSize:true,printBackground:true});
    const pdfInfo=execFileSync('pdfinfo',[path.join(dir,'review.pdf')],{encoding:'utf8'});
    assert.match(pdfInfo,/Pages:\s+1\b/);
    const pdfText=execFileSync('pdftotext',['-layout',path.join(dir,'review.pdf'),'-'],{encoding:'utf8'});
    for(const text of ['G036-NM','Near-Match','Uncomputed']) assert(pdfText.includes(text));
    assert(pdfText.replace(/\s/g,'').includes(near.input_sha256));
    await offline.close();

    // An edit removes exports immediately; missing Phase remains pre-search Uncomputed.
    await page.locator('input[name="target_wavefront_curvature_ts_per_m_0"]').fill('');
    await hidden();
    await design();
    assert.equal((await result()).status,'Uncomputed');
    assert.equal(await page.locator('#workflow-job').count(),0);

    await page.setViewportSize({width:393,height:852});
    const readinessPage=await openReference();
    assert(await readinessPage.getByText('Glass Waveguide External Port · Uncomputed',{exact:true}).isVisible());
    assert.match(await readinessPage.locator('#sun-fldw-55mw-1310').innerText(),/x 11 µm \/ y 18 µm/);
    assert.equal(await readinessPage.locator('#readiness-1310 svg').count(),0);
    await readinessPage.locator('#readiness-1310').scrollIntoViewIfNeeded();
    await readinessPage.screenshot({path:path.join(dir,'readiness-1310.png'),fullPage:true});
    await readinessPage.getByRole('link',{name:'검증한 Port 데이터로 새 입력 열기'}).click();
    await page.close();
    page=readinessPage;
    // Synthetic geometry and source input isolate the missing Glass Waveguide mode.
    const knownInputs={
      wavelength_m_0:'1310',ambient_index_0:'1',
      source_position_m_0:'0',source_position_m_1:'0',source_position_m_2:'0',
      source_propagation_direction_0:'1',source_propagation_direction_1:'0',source_propagation_direction_2:'0',
      source_mfd_ts_m_0:'20',source_wavefront_curvature_ts_per_m_0:'50',
      target_position_m_0:'2',target_position_m_1:'2',target_position_m_2:'0',
      target_propagation_direction_0:'1',target_propagation_direction_1:'0',target_propagation_direction_2:'0',
    };
    for(const [name,value] of Object.entries(knownInputs))
      await page.locator(`input[name="${name}"]`).fill(value);
    await design();
    const incomplete=await result();
    assert.equal(incomplete.status,'Uncomputed');
    assert.equal(incomplete.input_snapshot.target.mfd_ts_m.value,null);
    assert.equal(incomplete.input_snapshot.target.wavefront_curvature_ts_per_m.value,null);
    assert.equal(incomplete.selected_candidate_id,null);
    assert.equal(await page.locator('#workflow-job').count(),0);
    assert.equal(await frame().locator('[data-overlap-value]').count(),0);
    // Run both the original 1310 nm case and a single-coordinate edit through
    // the same installed Workspace and Worker that generated the 1550 nm result.
    await openR6();
    await design();
    const r6Job = await identity();
    await frame().locator('#design-result').waitFor({state:'attached', timeout:650000});
    const r6 = await result();
    assert.equal(r6.input_sha256, '20461fd9868b9450c0df7eff0464e6454a06811e5f09c244f4bc579d66efbcad');
    assert.equal(r6.input_sha256, cancelled.input_sha256);
    assert.equal(r6.input_sha256, r6Job.input_sha256);
    assert.equal(r6.reference_context.scope, 'Original');
    assert.equal(r6.selected_candidate_id, 'G036-NM');
    const originalSearch = r6.workflow.exact_search;
    assert.deepEqual([originalSearch.geometry_count, originalSearch.attempts.length, originalSearch.accepted_count], [36, 144, 0]);
    const eta = c => c.evaluation.gaussian_mode_matching.normalized_mode_overlap;
    assert(Math.abs(eta(r6.candidates[0]) - 0.9990889546173051) <= 1e-8);

    const z = page.locator('[name="target_position_m_2"]');
    await z.fill('2.1');
    await hidden();
    await design();
    const revisedJob = await identity();
    assert.notEqual(revisedJob.input_sha256, r6Job.input_sha256);
    await frame().locator('#design-result').waitFor({state:'attached', timeout:650000});
    const revised = await result();
    assert.equal(revised.workflow.state, 'Succeeded');
    assert.equal(revised.input_sha256, revisedJob.input_sha256);
    assert.deepEqual(revised.input_snapshot.source, r6.input_snapshot.source);
    assert.deepEqual(revised.input_snapshot.target.position_m.value, [0.002, 0, 0.0021]);
    assert.deepEqual(revised.input_snapshot.target.reference_plane.value.origin_m, [0.002, 0, 0.0021]);
    assert.deepEqual(revised.input_snapshot.target.mfd_ts_m, r6.input_snapshot.target.mfd_ts_m);
    assert.deepEqual(revised.input_snapshot.target.wavefront_curvature_ts_per_m,
      r6.input_snapshot.target.wavefront_curvature_ts_per_m);
    assert.equal(revised.input_snapshot.target.mode_evidence.value.kind, 'gaussian_assumption');
    assert.equal(revised.reference_context.scope, 'Edited');
    assert.deepEqual(revised.reference_context.changed_fields, ['Target Position']);
    assert.equal(revised.reference_context.reference_input_sha256, r6.input_sha256);
    const visibleCandidate = frame().locator('[data-candidate]:visible');
    assert.equal(await visibleCandidate.getAttribute('data-candidate'), revised.selected_candidate_id);
    assert.equal(await visibleCandidate.getAttribute('data-input-sha'), revised.input_sha256);
    assert(await frame().locator('[data-reference-scope="Edited"]').isVisible());
    const confidence = visibleCandidate.locator('[data-confidence]');
    await confidence.locator('summary').click();
    assert.match(await confidence.innerText(), new RegExp(revised.input_sha256));
    assert.match(await confidence.locator('tr').filter({hasText:'Total Coupling'}).innerText(), /Uncomputed/);

    for (const snapshot of [r6, revised]) {
      const current = snapshot.candidates[0];
      for (const name of ['source', 'target']) assert.deepEqual(current.prescription[name], snapshot.input_snapshot[name]);
      assert.equal(current.independent_validation.status, 'Pass');
      assert.equal(current.independent_validation.quadrature_overlap.length, 2);
      for (const overlap of current.independent_validation.quadrature_overlap)
        assert(Math.abs(eta(current) - overlap) <= 1e-8);
      execFileSync(process.env.PAE_PYTHON || 'python', ['-c', `
import json, sys
from photonic_architecture_explorer.external import evaluate_external
candidate = json.load(sys.stdin)
replayed = json.loads(json.dumps(evaluate_external(candidate["prescription"])))
published = candidate["evaluation"]
for key in published.keys() - {"input_snapshot"}:
    assert replayed[key] == published[key], key
`], {input: JSON.stringify(current), encoding:'utf8'});
    }
    const revisedJson = JSON.parse(fs.readFileSync(await exportFile('json', 'r6-edited')));
    assert.deepEqual(revisedJson, {...revised, viewed_candidate_id:revised.selected_candidate_id});
    const revisedHtml = await exportFile('html', 'r6-edited');
    const revisedOffline = await browser.newPage();
    await revisedOffline.goto(pathToFileURL(revisedHtml).href);
    assert.deepEqual(await revisedOffline.locator('#design-result').evaluate(e=>JSON.parse(e.textContent)), revisedJson);
    await revisedOffline.close();
    await page.screenshot({path:path.join(dir,'reference-1310-edited.png'),fullPage:true});

    await page.locator('[name="target_wavefront_curvature_ts_per_m_0"]').fill('');
    await hidden();
    await design();
    assert.equal((await result()).status, 'Uncomputed');
    assert.equal(await page.locator('#workflow-job').count(), 0);
    assert.equal(await frame().locator('[data-overlap-value]').count(), 0);
    await page.goto(address+'/?entry=smf-glass-1310');
    const envelopeEvidence = {};
    const checkClearance = (report, active, label) => {
      const selection = active.clearance_selection;
      const qualifies = label === 'expansion';
      assert.equal(selection.status, qualifies ? 'Verified' : 'NoTargetCandidate');
      if (qualifies) {
        assert.equal(selection.candidate.id, 'R8-expansion');
        assert.equal(selection.eligible_count, 1);
        assert(selection.quadrature.every(q => q >= 0.99 && Math.abs(q - active.overlap) <= 1e-8));
      } else {
        assert.equal(selection.candidate, null);
      }
      const winner = report.candidates[0];
      if (!winner) return {target_status:selection.status, additional_clearance_m:null};
      const {face, ...originalCheck} = winner.clearance.limiting_check;
      const checks = winner.evaluation.package_feasibility.envelope_geometry.checks;
      assert.deepEqual(checks.find(check => check.path === originalCheck.path), originalCheck);
      assert.equal(face, 'X-');
      const expected = label === 'midrange' ? 210e-6 : 0;
      assert(Math.abs(winner.clearance.additional_clearance_m - expected) <= 2e-12);
      return {target_status:selection.status, target_candidate:selection.candidate?.id ?? null,
        additional_clearance_m:winner.clearance.additional_clearance_m, limiting_check:originalCheck.path};
    };
    for (const key of ['nominal','expansion']) {
      await page.locator('[name="envelope"]').selectOption(key);
      await hidden();
      await design();
      const report = await result();
      const comparison = report.envelope_comparison;
      const active = comparison.cases[key];
      assert.equal(comparison.selected, key);
      assert.equal(report.input_sha256, active.input_sha256);
      assert.notEqual(report.input_sha256, r6.input_sha256);
      assert.equal(await frame().locator('#envelope-comparison > .table-scroll tbody tr').count(), 2);
      assert.equal(await frame().locator('.confidence code').textContent(), active.input_sha256);
      assert.equal(await frame().locator('.confidence').getAttribute('data-confidence'), active.selected);
      assert.equal(active.r9_replay.absolute_error <= 1e-8, true);
      assert.equal(active.threshold_met, key === 'expansion');
      const clearance = checkClearance(report, active, key);
      const envelopeTable = frame().locator('#envelope-comparison > .table-scroll tbody');
      assert.match(await envelopeTable.innerText(), /η 목표 충족 후보 없음/);
      assert.match(await envelopeTable.innerText(), /body\[1\]\.volume/);
      const saved = JSON.parse(fs.readFileSync(await exportFile('json', 'envelope-'+key)));
      assert.deepEqual(saved, {...report, viewed_candidate_id:active.selected});
      const offline = await browser.newPage();
      await offline.goto(pathToFileURL(await exportFile('html', 'envelope-'+key)).href);
      assert.deepEqual(await offline.locator('#design-result').evaluate(e=>JSON.parse(e.textContent)),saved);
      assert.equal(await offline.locator('#pose-envelope code').textContent(), report.input_sha256);
      await offline.close();
      const pose = report.pose_envelope;
      assert.equal(pose.status, 'Verified');
      assert.equal(pose.input_sha256, report.input_sha256);
      assert.equal(pose.pose_count, 13);
      assert.equal(pose.cases.length, 13);
      assert(pose.cases.every(row => row.status === 'Pass' && row.minimum_gap_m >= 50e-6));
      assert(Math.abs(pose.suggestion.x_min_change_m + 5e-6) <= 2e-12);
      assert(Math.abs(pose.suggestion.x_max_change_m - 5e-6) <= 2e-12);
      assert(Math.abs(pose.suggestion.width_increase_m - 10e-6) <= 2e-12);
      assert.deepEqual(pose.limiting_sides.map(side => [side.pose, side.face]),
        [['M2 X -5 µm', 'X-'], ['M1 X +5 µm', 'X+']]);
      assert.equal(await frame().locator('#pose-envelope code').textContent(), report.input_sha256);
      assert.equal(await frame().locator('#pose-envelope').getAttribute('data-status'), 'Verified');
      envelopeEvidence[key] = {input_sha256:active.input_sha256, candidate:active.selected,
        passed:active.passing_trials.length, evaluated:active.evaluations, eta:active.overlap,
        quadrature:active.quadrature, gap_m:active.minimum_gap_m, radius_m:active.max_projected_radius_m,
        clearance, pose_envelope:{input_sha256:pose.input_sha256, pose_count:pose.pose_count,
          suggestion:pose.suggestion, limiting_sides:pose.limiting_sides}};
    }
    assert.notEqual(envelopeEvidence.nominal.input_sha256,envelopeEvidence.expansion.input_sha256);
    const sizingEvidence = {};
    for (const [goal, expectedIncrease] of [[0,0], [50,.0001], [100,.0002], [500,null]]) {
      await page.getByRole('textbox', {name:/추가 AABB Clearance 목표/}).fill(String(goal));
      await hidden();
      await design();
      const report = await result();
      const sizing = report.envelope_sizing;
      const suggested = sizing.suggestion;
      assert.equal(report.input_sha256, envelopeEvidence.expansion.input_sha256);
      assert.equal(report.search_policy.maximum_trials_per_envelope, 74);
      assert.equal(sizing.target_additional_m, Number(goal+'e-6'));
      assert.equal(await frame().locator('.confidence code').textContent(), report.input_sha256);
      assert.equal(await frame().locator('#envelope-sizing').getAttribute('data-status'), sizing.status);
      if (expectedIncrease !== null) {
        assert.equal(sizing.status, 'Verified');
        assert(Math.abs(suggested.width_increase_m - expectedIncrease) <= 2e-12);
        assert(suggested.quadrature.every(q => q >= 0.99 && Math.abs(q - suggested.eta) <= 1e-8));
        assert.equal(suggested.adapter_checks.every(check => check.status === 'Pass'), true);
        assert.equal(await frame().locator('#envelope-sizing code').textContent(), suggested.prescription_sha256);
      } else {
        assert.equal(sizing.status, 'Limited');
        assert.equal(suggested, null);
        assert.equal(sizing.limiting_check.path, 'body[1].volume');
        assert.equal(sizing.limiting_check.face, 'Z+');
        assert.equal(sizing.limiting_check.status, 'Fail');
      }
      if (goal === 100 || goal === 500) {
        const saved = JSON.parse(fs.readFileSync(await exportFile('json', 'envelope-sizing-'+goal)));
        assert.deepEqual(saved, {...report, viewed_candidate_id:report.selected_candidate_id});
        const offline = await browser.newPage();
        await offline.goto(pathToFileURL(await exportFile('html', 'envelope-sizing-'+goal)).href);
        assert.deepEqual(await offline.locator('#design-result').evaluate(e=>JSON.parse(e.textContent)),saved);
        await offline.close();
      }
      sizingEvidence[goal] = {status:sizing.status, maximum_additional_m:sizing.maximum_additional_m,
        x_min_m:suggested?.x_min_m ?? null, x_max_m:suggested?.x_max_m ?? null,
        width_increase_m:suggested?.width_increase_m ?? null, eta:suggested?.eta ?? null,
        quadrature:suggested?.quadrature ?? null, proposal_sha:suggested?.prescription_sha256 ?? null,
        limiting_check:sizing.limiting_check};
    }
    assert.equal(new Set([0,50,100].map(goal=>sizingEvidence[goal].proposal_sha)).size,3);
    await page.getByRole('textbox', {name:/추가 AABB Clearance 목표/}).fill('');
    const customEvidence = {};
    const setXBounds = async (min, max) => {
      await page.locator('[name="envelope_x_min_mm"]').fill(min);
      await page.locator('[name="envelope_x_max_mm"]').fill(max);
      await hidden();
      await design();
    };
    await page.locator('[name="envelope"]').selectOption('custom');
    for (const [label, min, max, passed, winner] of [
      ['nominal', '-1.15', '3.15', 19, 'R8-nominal'],
      ['expansion', '-1.5821774231937228', '3.4415473764667017', 48, 'R8-expansion'],
      ['midrange', '-1.36', '3.37', 37, 'R8-nominal'],
      ['narrow', '0', '2', 0, null],
    ]) {
      await setXBounds(min, max);
      const report = await result();
      const active = report.envelope_comparison.cases.custom;
      const volume = report.input_snapshot.package.available_volume;
      assert.equal(volume.provenance, 'supplied');
      assert.equal(volume.value.min_m[0], Number(min + 'e-3'));
      assert.equal(volume.value.max_m[0], Number(max + 'e-3'));
      assert.equal(active.input_sha256, report.input_sha256);
      assert.equal(active.passing_trials.length, passed);
      assert.equal(active.evaluations, 74);
      assert.equal(active.selected, winner);
      assert.equal(report.status, winner ? 'Computed' : 'NoCandidate');
      if (winner) {
        assert.equal(await frame().locator('.confidence code').textContent(), report.input_sha256);
        assert.equal(await frame().locator('.confidence').getAttribute('data-confidence'), winner);
        assert(active.quadrature.every(q => Math.abs(q - active.overlap) <= 1e-8));
      } else {
        assert.equal(await frame().locator('.confidence').count(), 0);
        assert.match(await frame().locator('#envelope-comparison').innerText(), /통과 후보 없음/);
        assert.equal(active.overlap, null);
      }
      if (envelopeEvidence[label]) {
        assert(active.r9_replay.absolute_error <= 1e-8);
        assert.equal(active.overlap, envelopeEvidence[label].eta);
      } else {
        assert.equal(active.r9_replay, null);
      }
      if (label === 'midrange' || label === 'narrow') {
        const saved = JSON.parse(fs.readFileSync(await exportFile('json', 'custom-'+label)));
        assert.deepEqual(saved, winner ? {...report, viewed_candidate_id:winner} : report);
        const offline = await browser.newPage();
        await offline.goto(pathToFileURL(await exportFile('html', 'custom-'+label)).href);
        assert.deepEqual(await offline.locator('#design-result').evaluate(e=>JSON.parse(e.textContent)), saved);
        await offline.close();
      }
      const clearance = checkClearance(report, active, label);
      customEvidence[label] = {bounds_m:[volume.value.min_m[0],volume.value.max_m[0]],
        input_sha256:active.input_sha256, passed, selected:winner, status:report.status,
        eta:active.overlap, quadrature:active.quadrature, gap_m:active.minimum_gap_m, clearance};
    }
    assert.equal(new Set(Object.values(customEvidence).map(row => row.input_sha256)).size, 4);
    await setXBounds('2','2');
    assert.match(await page.locator('[role="alert"]').innerText(), /입력 오류.*min은 max보다 작아야/);
    assert.equal(await page.locator('[data-export]').count(),0);
    await page.locator('[name="envelope"]').selectOption('expansion');
    await page.locator('[name="target_position_m_2"]').fill('2.1');
    await hidden();
    await design();
    assert.match(await page.locator('[role="alert"]').innerText(), /원본 Example A/);
    assert.equal(await page.locator('[data-export]').count(),0);
    const r6Evidence = snapshot => {
      const current = snapshot.candidates[0];
      return {input_sha256:snapshot.input_sha256, selected:snapshot.selected_candidate_id,
        target_position_m:snapshot.input_snapshot.target.position_m.value,
        exact_geometries:snapshot.workflow.exact_search.geometry_count,
        exact_attempts:snapshot.workflow.exact_search.attempts.length,
        adapter_calls:snapshot.workflow.near_match.adapter_calls, overlap:eta(current),
        quadrature:current.independent_validation.quadrature_overlap,
        path_m:current.ranking.total_path_m, elapsed_seconds:snapshot.workflow.elapsed_seconds};
    };

    assert.deepEqual(errors,[]);
    const evidence={status:'Pass',head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
      cancelled,edited,completed,selected:near.selected_candidate_id,
      overlap:candidate.evaluation.gaussian_mode_matching.normalized_mode_overlap,
      elapsed_seconds:near.workflow.elapsed_seconds,all_36_summaries_equal:true,
      input_edit_and_late_reply_withheld:true,export_equal:true,a4_pages:1,browser_errors:errors,
      http_ping_ms:pingMs,identity_checks:'job ID + revision + SHA',
      reference_handoff:{concept_1550:'Reference → Proxy → Design → Background Near-Match',
        incomplete_1310:incomplete.status,worker_started_for_incomplete_1310:false},
      envelope_comparison:envelopeEvidence, custom_x_bounds:customEvidence, envelope_sizing:sizingEvidence,
      r6_redesign:{original:r6Evidence(r6),edited:r6Evidence(revised),adapter_replay_equal:true,
        export_equal:true, confidence_scope:'Edited input SHA', missing_phase:'Uncomputed'}};
    fs.writeFileSync(path.join(dir,'acceptance.json'),JSON.stringify(evidence,null,2)+'\n');
    console.log(JSON.stringify(evidence));

    async function expectTerminal(id,wanted){
      for(let i=0;i<100;i++){
        const data=await status(id);
        if(['Cancelled','TimedOut','Failed','Succeeded','NoCandidate'].includes(data.state)){
          assert.equal(data.state,wanted);assert.equal(data.report_html,undefined);return;
        }
        await page.waitForTimeout(100);
      }
      throw new Error('Cancellation did not complete');
    }
  } finally {
    if(browser) await browser.close();
    server.kill('SIGTERM');
    await new Promise(resolve=>{server.once('exit',resolve);setTimeout(resolve,5000)});
  }
}
main().catch(error=>{console.error(error);process.exit(1)});
