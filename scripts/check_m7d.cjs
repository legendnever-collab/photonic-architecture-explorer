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
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
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
    await page.goto(address);
    await design();
    const exact=await result();
    assert.equal(exact.selected_candidate_id,'G009-B1');
    assert.equal(await page.locator('#workflow-job').count(),0);
    const exactHTML=await page.locator('#design-review').getAttribute('srcdoc');

    // Start an actual eligible job and cancel it from the Desktop UI.
    await page.goto(address+'/?entry=smf-glass');
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
    await page.goto(address+'/?entry=smf-glass');
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

    // Retry unchanged Proxy inputs: fresh ID, same SHA, full real search (no fixture result cache).
    await page.goto(address+'/?entry=smf-glass');
    await design();
    const completed=await identity();
    assert.notEqual(completed.job_id,cancelled.job_id);
    assert.notEqual(completed.revision,edited.revision);
    assert.equal(completed.input_sha256,cancelled.input_sha256);
    await hidden();
    await frame().locator('#design-result').waitFor({state:'attached',timeout:650000});
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
    const exportFile=async format=>{
      const downloadPromise=page.waitForEvent('download');
      await page.locator('[data-export="'+format+'"]').click();
      const download=await downloadPromise;
      const target=path.join(dir,'design.'+format);
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
    assert.deepEqual(errors,[]);
    const evidence={status:'Pass',head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
      cancelled,edited,completed,selected:near.selected_candidate_id,
      overlap:candidate.evaluation.gaussian_mode_matching.normalized_mode_overlap,
      elapsed_seconds:near.workflow.elapsed_seconds,all_36_summaries_equal:true,
      input_edit_and_late_reply_withheld:true,export_equal:true,a4_pages:1,browser_errors:errors,
      http_ping_ms:pingMs,identity_checks:'job ID + revision + SHA'};
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
