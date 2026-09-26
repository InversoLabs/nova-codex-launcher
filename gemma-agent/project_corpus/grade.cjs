// Run candidate JavaScript only in an isolated browser context, never as Node code.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const [manifestFile,projectId,workspace,output]=process.argv.slice(2);
const manifest=JSON.parse(fs.readFileSync(manifestFile,'utf8'));
const project=manifest.projects.find(p=>p.id===projectId);
if(!project) throw Error('Unknown project');
const root=path.resolve(workspace);
const allowed=new Set(['index.html','style.css','logic.js','app.js']);
const report={schema:1,project:projectId,passed:false,checks:[],errors:[]};
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.CORPUS_BROWSER_CHANNEL||'msedge'});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block',acceptDownloads:false});
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   const name=decodeURIComponent(url.pathname.slice(1)||'index.html');
   if(url.origin!=='http://corpus.test'||!allowed.has(name)) return route.abort();
   const file=path.join(root,name);
   try{if(fs.lstatSync(file).isSymbolicLink())return route.abort();
    await route.fulfill({status:200,contentType:name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':'application/javascript',body:fs.readFileSync(file)});
   }catch{return route.fulfill({status:404,body:'Not found'});}
  });
  const page=await context.newPage();page.setDefaultTimeout(4000);
  const runtimeErrors=[];page.on('pageerror',e=>runtimeErrors.push(e.message));
  await page.goto('http://corpus.test/');
  for(let i=0;i<project.cases.length;i++){
   try{
    const [input,expected]=project.cases[i];
    for(const [key,value] of Object.entries(input)) await page.locator(`[name="${key}"]`).fill(value);
    await page.locator('button[type=submit]').click();
    assert.equal(await page.locator('#error').innerText(),'','Unexpected form error');
    for(const [key,value] of Object.entries(expected)) assert.equal(await page.locator(`[data-metric="${key}"]`).innerText(),String(value),key);
    assert.equal(await page.locator('#result dd').count(),Object.keys(expected).length);
    report.checks.push('behavior case '+(i+1));
   }catch(e){report.errors.push('case '+(i+1)+': '+e.message.slice(0,500));}
  }
  const numeric=project.fields.find(f=>f[2]==='number');
  if(numeric){
   try{await page.locator(`[name="${numeric[0]}"]`).fill('');await page.locator('button[type=submit]').click();assert.ok((await page.locator('#error').innerText()).length>0);assert.equal(await page.locator('#result dd').count(),0);report.checks.push('invalid input clears stale results');}
   catch(e){report.errors.push('validation: '+e.message.slice(0,500));}
  }
  try{
   await page.locator('#reset').click();
   for(const [name,,,value] of project.fields) assert.equal(await page.locator(`[name="${name}"]`).inputValue(),value);
   assert.equal(await page.locator('#result dd').count(),0);assert.equal(await page.locator('#error').innerText(),'');
   report.checks.push('reset restores defaults');
   const [input,expected]=project.cases[0];
   for(const [key,value] of Object.entries(input))await page.locator(`[name="${key}"]`).fill(value);
   await page.locator('button[type=submit]').click();await page.reload();
   if(project.id==='password-meter')assert.equal(await page.locator('#history li').count(),0);
   else assert.equal(await page.locator('#history li').innerText(),Object.values(expected).join(' · '));
   await page.locator('#clear').click();await page.reload();assert.equal(await page.locator('#history li').count(),0);
   report.checks.push('persistence and clear');
  }catch(e){report.errors.push('state: '+e.message.slice(0,500));}
  try{
   for(const [name] of project.fields)assert.ok(await page.locator(`label[for="${name}"]`).count());
   await page.locator('button[type=submit]').focus();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');assert.ok(await page.locator('button[type=submit]').evaluate(e=>e.matches(':focus-visible')));
   await page.setViewportSize({width:375,height:812});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.emulateMedia({reducedMotion:'reduce'});
   report.checks.push('labels, keyboard focus, mobile overflow');
   if(output)await page.screenshot({path:output.replace(/\.json$/,'.png'),fullPage:true});
  }catch(e){report.errors.push('layout: '+e.message.slice(0,500));}
  report.errors.push(...runtimeErrors.map(e=>'runtime: '+e));
  report.passed=report.errors.length===0;
 }finally{await browser.close();}
})().catch(e=>report.errors.push(e.stack)).finally(()=>{
 if(output)fs.writeFileSync(output,JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));process.exitCode=report.passed?0:1;
});
