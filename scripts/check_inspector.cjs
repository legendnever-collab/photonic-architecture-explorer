const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
(async()=>{
 const {spawn} = require('node:child_process');
 const server = spawn('python', ['-m','photonic_architecture_explorer.inspector','--serve','--port','8765'], {env:{...process.env,PYTHONPATH:'src'},stdio:['ignore','pipe','inherit']});
 await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',code=>reject(new Error('server exited '+code)));});
 try {
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1050}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765');
 const active=()=>page.locator('article[data-case]:visible');
 assert.equal(await active().locator('[data-overlap-value]').innerText(),'1');
 const nominalPorts=JSON.parse(await active().locator('textarea[name=ports]').inputValue());
 await page.screenshot({path:'results/inspector_desktop.png',fullPage:true});
 const report={browser:await browser.version(),desktop:{width:1440,height:1050},mobile:{width:393,height:852},checks:[]};
 for(const proj of ['XY','YZ','XZ']){
  await page.selectOption('#projection-select',proj);
  assert.equal(await active().locator('.projection:visible').count(),1);
  assert((await active().locator('.projection:visible h3').innerText()).startsWith(proj));
 }report.checks.push('all 3 projections and omitted-axis labels');
 for(const key of ['blank','missing-phase','bad-unit','target-direction','high-divergence','bounds-fail','package-fail']){
  await page.selectOption('#case-select',key);
  assert.equal(await page.locator('[data-overlap-value]:visible').count(),0,key);
  assert.equal(await active().locator('[data-overlap-withheld]').count(),1,key);
  if(key==='target-direction')assert.equal(await active().locator('[data-kind=verified-chief]').count(),0);
  const inputPath={'bad-unit':'source.position_m','blank':'wavelength_m','missing-phase':'source'}[key];
  if(inputPath){
   const reason=active().locator('.results details').filter({hasText:'판정 근거 / 미계산 항목'});
   await reason.locator('summary').click();
   assert.equal(await reason.locator('code.issue-path').innerText(),inputPath);
   assert.equal(await reason.locator('code.issue-path').isVisible(),true);
  }
  await page.selectOption('#case-select','nominal');
  assert.equal(await page.locator('[data-overlap-value]:visible').count(),1);
 }report.checks.push('7 invalid/unprovided cases with no previous overlap; nominal restored each time');
 report.checks.push('human diagnostics expose exact Adapter input path for unit/missing-data failures');
 // Engineering recovery: locate the rejected field, correct its unit, reevaluate.
 await page.selectOption('#case-select','bad-unit');
 await page.screenshot({path:'results/inspector_input_diagnostic_desktop.png',fullPage:true});
 await active().locator('details').filter({has:page.locator('textarea[name=ports]')}).locator('summary').click();
 const fixedUnit=JSON.parse(await active().locator('textarea[name=ports]').inputValue());
 fixedUnit.source.position_m.unit='m';
 await active().locator('textarea[name=ports]').fill(JSON.stringify(fixedUnit,null,2));
 assert.equal(await page.locator('[data-overlap-value]:visible').count(),0);
 await active().locator('button[type=submit]').click();
 await page.waitForURL('**/evaluate');
 assert.equal(await active().locator('[data-overlap-value]').innerText(),'1');
 assert.deepEqual(JSON.parse(await active().locator('textarea[name=ports]').inputValue()),nominalPorts);
 report.checks.push('bad unit → visible source.position_m → explicit unit correction → overlap restored with identical Ports');
 await page.goto('http://127.0.0.1:8765');
 // Open editor, change one design variable, ensure stale output disappears BEFORE submit.
 await active().locator('details').filter({has:page.locator('textarea[name=reflectors]')}).locator('summary').click();
 let text=await active().locator('textarea[name=reflectors]').inputValue();
 const design=JSON.parse(text);design.design.reflectors[0].principal_curvature_ts_per_m.value[0]*=1.01;
 await active().locator('textarea[name=reflectors]').fill(JSON.stringify(design,null,2));
 assert.equal(await active().locator('.results:visible').count(),0);
 assert.equal(await active().locator('.projection-group:visible').count(),0);
 assert.equal(await active().locator('[data-evaluated]:visible').count(),0);
 await active().locator('button[type=submit]').click();
 await page.waitForURL('**/evaluate');
 let eta=Number(await active().locator('[data-overlap-value]').innerText());
 assert(eta<1 && eta>0.99,String(eta));
 assert.deepEqual(JSON.parse(await active().locator('textarea[name=ports]').inputValue()),nominalPorts);
 report.changed_overlap=eta;report.checks.push('explicit curvature edit reevaluates via Python; Fixed Ports remain identical');
 await active().locator('details').filter({has:page.locator('textarea[name=ports]')}).locator('summary').click();
 const savedPorts=await active().locator('textarea[name=ports]').inputValue();
 await active().locator('textarea[name=ports]').fill('{');
 assert.equal(await page.locator('[data-overlap-value]:visible').count(),0);
 await active().locator('button[type=submit]').click();
 await page.waitForLoadState('load');
 assert.equal(await page.locator('[data-overlap-value]').count(),0);
 assert((await active().innerText()).includes('Input Contract'));
 const syntaxReason=active().locator('.results details').filter({hasText:'판정 근거 / 미계산 항목'});
 await syntaxReason.locator('summary').click();
 assert.equal(await syntaxReason.locator('code.issue-path').innerText(),'JSON editor');
 await active().locator('details').filter({has:page.locator('textarea[name=ports]')}).locator('summary').click();
 await active().locator('textarea[name=ports]').fill(savedPorts);
 await active().locator('button[type=submit]').click();
 await page.waitForLoadState('load');
 assert.equal(await page.locator('[data-overlap-value]:visible').count(),1);
 report.checks.push('valid → invalid JSON → valid edit; stale plot/summary/digest/results withheld');
 await page.goto('http://127.0.0.1:8765');
 await page.setViewportSize({width:393,height:852});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth),true);
 for(const key of ['nominal','package-fail','blank','bad-unit']){
  await page.selectOption('#case-select',key);
  if(key==='bad-unit'){
   const reason=active().locator('.results details').filter({hasText:'판정 근거 / 미계산 항목'});
   await reason.locator('summary').click();
   assert.equal(await reason.locator('code.issue-path').innerText(),'source.position_m');
   await page.screenshot({path:'results/inspector_input_diagnostic_mobile.png',fullPage:true});
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth),true,key);
 }
 await page.selectOption('#case-select','nominal');
 await page.screenshot({path:'results/inspector_mobile.png',fullPage:true});
 report.checks.push('mobile layout/selectors without horizontal overflow at 393 px');
 await page.goto('file://'+require('node:path').resolve('results/m3b-inspector.html'));
 assert.equal(await page.locator('[data-overlap-value]:visible').count(),1);
 await page.selectOption('#case-select','bounds-fail');
 assert.equal(await page.locator('[data-overlap-value]:visible').count(),0);
 await page.selectOption('#projection-select','YZ');
 assert.equal(await page.locator('article:visible .projection:visible').count(),1);
 await page.selectOption('#case-select','bad-unit');
 const staticReason=active().locator('.results details').filter({hasText:'판정 근거 / 미계산 항목'});
 await staticReason.locator('summary').click();
 assert.equal(await staticReason.locator('code.issue-path').innerText(),'source.position_m');
 await page.screenshot({path:'results/inspector_input_diagnostic_static.png',fullPage:true});
 report.checks.push('portable static HTML file: case/projection selection without server');
 assert.deepEqual(errors,[]);report.page_errors=errors;report.status='Pass';
 fs.writeFileSync('results/m3b_browser.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));await browser.close();
 } finally { server.kill(); }
})().catch(e=>{console.error(e);process.exit(1)});
