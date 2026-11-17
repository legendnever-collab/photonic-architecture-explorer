// Read-only static report: all physics and design data come from Python.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const dir=process.argv[2];assert(dir,'supply fresh M5-A artifact directory');
 const source=JSON.parse(fs.readFileSync(path.join(dir,'design.json'),'utf8'));
 const provenance=JSON.parse(fs.readFileSync(path.join(dir,'provenance.json'),'utf8'));
 assert.equal(provenance.status,'Pass');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox'],executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  // No server or external assets; the downloaded HTML must stand alone.
  await page.route('http**://**/*',route=>route.abort());
  await page.goto('file://'+path.resolve(dir,'design.html'));
  assert.deepEqual(await page.locator('#design-result').evaluate(el=>JSON.parse(el.textContent)),source);
  assert.equal(await page.locator('#candidate-select').inputValue(),source.selected_candidate_id);
  assert.equal(await page.locator('textarea,button[type=submit]').count(),0);
  for(const c of source.candidates){
   await page.selectOption('#candidate-select',c.id);
   const active=page.locator('[data-candidate]:visible');
   assert.equal(await active.count(),1);
   assert.equal(Number(await active.locator('[data-overlap-value]:visible').innerText()),c.evaluation.gaussian_mode_matching.normalized_mode_overlap);
   for(const proj of ['XZ','XY','YZ']){
    await page.selectOption('#projection-select',proj);
    assert.equal(await active.locator('.projection:visible').count(),1);
    assert.equal(await active.locator('.projection:visible').getAttribute('data-projection'),proj);
   }
  }
  await page.selectOption('#candidate-select',source.selected_candidate_id);
  await page.selectOption('#projection-select','XZ');
  for(const viewport of [{width:1440,height:1050},{width:393,height:852}]){
   await page.setViewportSize(viewport);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(dir,`design-${viewport.width}.png`),fullPage:true});
  }
  for(const name of ['missing-phase','domain-fail']){
   await page.goto('file://'+path.resolve(dir,name+'.html'));
   assert.equal(await page.locator('[data-overlap-value]').count(),0);
   assert.equal(await page.locator('[data-design-failure]').count(),1);
   const expected=JSON.parse(fs.readFileSync(path.join(dir,name+'.json'),'utf8'));
   assert.deepEqual(await page.locator('#design-result').evaluate(el=>JSON.parse(el.textContent)),expected);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  }
  assert.deepEqual(errors,[]);
  const evidence={status:'Pass',evaluated_checkout_sha:provenance.evaluated_checkout_sha,browser:await browser.version(),
   checks:['exact embedded JSON','automatic initial selection','3 candidates × 3 projections','no physics editor or network dependency','desktop/mobile no overflow','failure reports with no overlap'],page_errors:errors};
  fs.writeFileSync(path.join(dir,'browser.json'),JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify(evidence));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
