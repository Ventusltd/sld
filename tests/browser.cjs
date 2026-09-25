/* Run in Linux CI against the packaged site. Do not launch local Windows Chromium. */
'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const base=process.env.BASE_URL||'http://127.0.0.1:8765';
(async()=>{
  if(process.platform==='win32'&&!process.env.ALLOW_LOCAL_BROWSER)throw Error('Use remote Linux CI; local Windows browser launch is disabled.');
  const browser=await chromium.launch({headless:true});
  const errors=[];
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    const requests=[];page.on('request',request=>requests.push(request.url()));
    await page.goto(base);await page.waitForFunction(()=>document.querySelectorAll('.card').length===35);
    assert.match(await page.locator('.notice').innerText(),/disabled for production/);
    assert.equal(await page.locator('#furnace').count(),0);
    assert.doesNotMatch(await page.locator('body').innerText(),/furnace|GPU|photon|receipt/i);
    assert.equal(requests.some(url=>url.includes('/data/furnace/')),false,'The public UI must not fetch receipts');
    assert.equal(await page.getByRole('link',{name:'Source code',exact:true}).getAttribute('href'),'https://github.com/Ventusltd/sld');
    const palette=await page.evaluate(()=>{const body=getComputedStyle(document.body),link=getComputedStyle(document.querySelector('nav a')),button=getComputedStyle(document.querySelector('button'));return {background:body.backgroundColor,text:body.color,link:link.color,font:body.fontFamily,buttonFont:button.fontFamily,highlight:getComputedStyle(document.documentElement).getPropertyValue('--highlight').trim()};});
    assert.equal(palette.background,'rgb(0, 0, 0)');assert.equal(palette.text,'rgb(255, 255, 255)');assert.equal(palette.link,'rgb(102, 204, 255)');assert.equal(palette.highlight,'#00ffff');
    assert.equal(palette.font,'ui-monospace, SFMono-Regular, Consolas, monospace');assert.equal(palette.buttonFont,'ui-monospace, monospace');
    await page.locator('.card').first().locator('summary').click();assert.match(await page.locator('.card').first().innerText(),/MPL-2.0/);
    // Each generated SVG is fetched independently, including lazy images below the fold.
    for(const src of await page.locator('.preview').evaluateAll(imgs=>imgs.map(i=>i.getAttribute('src'))))assert.equal((await page.request.get(new URL(src,base+'/').href)).status(),200,src);
    await page.locator('#search').fill('breaker');assert.equal(await page.locator('.card').count(),1);
    await page.getByRole('button',{name:'+ Add to draft',exact:true}).click();
    await page.locator('#search').fill('not-a-part-xyz');assert.equal(await page.locator('.card').count(),0);assert.equal(await page.locator('#empty').isVisible(),true);
    await page.locator('#search').fill('two_windings');assert.equal(await page.locator('.card').count(),1);await page.getByRole('button',{name:'+ Add to draft',exact:true}).click();
    assert.equal(await page.locator('.instance').count(),2);
    const before=await page.locator('.instance.selected').getAttribute('transform');await page.locator('#move-right').click();assert.notEqual(await page.locator('.instance.selected').getAttribute('transform'),before);
    await page.locator('#connect').click();await page.locator('.instance').nth(0).click();await page.locator('.instance').nth(1).click();assert.equal(await page.locator('#canvas>line').count(),1);
    const exported=page.waitForEvent('download');await page.locator('#export').click();const file=await exported;const json=JSON.parse(await fs.readFile(await file.path(),'utf8'));assert.equal(json.instances.length,2);assert.equal(json.connections[0].kind,'illustrative-centre-link');
    await page.locator('#clear').click();assert.equal(await page.locator('.instance').count(),0);
    await page.locator('#import').setInputFiles({name:'draft.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(json))});await page.waitForFunction(()=>document.querySelectorAll('.instance').length===2);
    const invalid={...json,instances:[{...json.instances[0],component_id:'<img src=x onerror=alert(1)>'}]};await page.locator('#import').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalid))});await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Import rejected'));assert.equal(await page.locator('.instance').count(),2);
    const polluted={...json,html:'<script>window.injected=true</script>'};await page.locator('#import').setInputFiles({name:'extra.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(polluted))});await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Imported'));assert.equal(await page.evaluate(()=>window.injected),undefined);
    const svgDownload=page.waitForEvent('download');await page.locator('#export-svg').click();const svgText=await fs.readFile(await (await svgDownload).path(),'utf8');assert.match(svgText,/EDUCATIONAL DRAFT/);assert.match(svgText,/data:image\/svg\+xml;base64,/);assert.doesNotMatch(svgText,/href="assets\//);
    await page.locator('.instance').first().click();await page.locator('#delete').click();assert.equal(await page.locator('.instance').count(),1);assert.equal(await page.locator('#canvas>line').count(),0);
    await page.locator('#search').fill('');await page.evaluate(()=>scrollTo(0,0));
    await fs.mkdir('artifacts',{recursive:true});await page.screenshot({path:path.join('artifacts','desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});await page.locator('#search').fill('ground');assert.equal(await page.locator('.card').count(),2);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'mobile page must not overflow horizontally');await page.locator('#search').fill('');await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join('artifacts','mobile.png'),fullPage:true});
    assert.deepEqual(errors,[]);console.log('PASS: 35 previews, provenance, search, draft edits, links, safe import/export, standalone SVG, desktop/mobile and console.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
