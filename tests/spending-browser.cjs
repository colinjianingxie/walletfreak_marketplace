const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {mkdtempSync,readFileSync,rmSync,mkdirSync}=require('node:fs');
const {join,resolve}=require('node:path');
const {tmpdir}=require('node:os');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const data=mkdtempSync(join(tmpdir(),'walletfreak-spending-test-')),root=resolve(__dirname,'..'),script=join(root,'plugins/walletfreak/scripts/local.py'),env={...process.env,WALLETFREAK_DATA:data};
 const cli=(...args)=>execFileSync('python3',[script,...args],{env,encoding:'utf8'}).trim();let browser;
 try{
  const url=cli('start','--port','0'),descriptor=JSON.parse(readFileSync(join(data,'server.json')));
  browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const context=await browser.newContext(),page=await context.newPage(),errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(new URL(url).origin))external.push(r.url());});
  await page.goto(url);await page.getByRole('button',{name:'Finance',exact:true}).click();await page.locator('#spend-advanced > summary').click();await page.locator('#spend-import-panel > summary').click();await page.getByText('0 matching · 0 total').waitFor();
  await page.getByLabel('Account alias',{exact:true}).fill('Test personal');
  const content='Transaction Date,Description,Category,Type,Amount\n10/01/2026,Cafe,Dining,Sale,-12.34\n10/02/2026,Payment Thank You,,Payment,30\n10/03/2026,Refund,Dining,Return,2.34\n10/04/2026,Unknown credit,,,5\n';
  const file={name:'synthetic.csv',mimeType:'text/csv',buffer:Buffer.from(content)};
  await page.getByLabel('Activity CSV').setInputFiles(file);await page.getByRole('button',{name:'Preview import',exact:true}).click();await page.getByText('4 transactions · 0 possible duplicates').waitFor();
  assert.match(await page.locator('#spend-preview').innerText(),/12.34/);
  await page.getByRole('button',{name:'Add preview to ledger'}).click();await page.getByText('4 matching · 4 total').waitFor();
  await page.getByRole('button',{name:'Approve this page'}).click();await page.getByText('Spending edits saved locally.',{exact:true}).waitFor();
  assert.match(await page.locator('#spend-totals').innerText(),/10.00/);
  const row=page.locator('#spend-table tbody tr').filter({hasText:'Unknown credit'});assert.equal(await row.locator('[data-spend-field=review]').inputValue(),'needs-review');
  await row.locator('[data-spend-field=type]').selectOption('refund');await row.locator('[data-spend-field=category]').fill('Dining');await row.locator('[data-spend-field=review]').selectOption('approved');await page.getByRole('button',{name:'Save row edits',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#spend-totals').textContent.includes('5.00'));
  await page.getByLabel('Activity CSV').setInputFiles(file);await page.getByRole('button',{name:'Preview import',exact:true}).click();await page.getByText('This file and mapping were already imported.',{exact:true}).waitFor();assert.equal(await page.locator('#spend-confirm').isVisible(),false);
  await page.getByLabel('Activity CSV').setInputFiles({...file,name:'overlap.csv',buffer:Buffer.from(content+'10/05/2026,Hotel,Travel,Sale,-100\n')});await page.getByRole('button',{name:'Preview import',exact:true}).click();await page.getByText('5 transactions · 4 possible duplicates').waitFor();await page.getByRole('button',{name:'Add preview to ledger'}).click();await page.getByText('9 matching · 9 total').waitFor();
  await page.getByRole('button',{name:'Approve this page'}).click();await page.waitForFunction(()=>document.querySelector('#spend-totals').textContent.includes('100.00'));
  const snapshot=JSON.parse(readFileSync(join(data,'spending.json')));assert.equal(snapshot.rows.filter(r=>r.possible_duplicate&&r.review==='approved').length,0);
  const a=await page.request.get(new URL('/api/spending/transactions.csv',url).href);assert.equal(a.status(),200);assert.match(await a.text(),/source_category/);
  const summary=await page.request.get(new URL('/api/spending/summary.csv',url).href);assert.match(await summary.text(),/Dining,5.00/);
  const anonymous=await browser.newContext();for(const path of ['/api/spending','/api/spending/transactions.csv','/api/spending/summary.csv']){
   assert.equal((await anonymous.request.get(new URL(path,url).href)).status(),401);
   assert.equal((await anonymous.request.get(new URL(path,url).href,{headers:{Authorization:'Bearer '+descriptor.agent_token}})).status(),403);
  }
  const denied=await anonymous.request.post(new URL('/api/spending/delete',url).href,{headers:{Authorization:'Bearer '+descriptor.agent_token,'X-WalletFreak':'1'},data:{expected_revision:snapshot.revision,confirm:'delete-spending'}});assert.equal(denied.status(),403);await anonymous.close();
  const other=await context.newPage();await other.goto(url);await other.getByRole('button',{name:'Finance',exact:true}).click();await other.locator('#spend-advanced > summary').click();await other.getByText('9 matching · 9 total').waitFor();
  const first=page.locator('#spend-table tbody tr').first();await first.locator('[data-spend-field=category]').fill('Edited category');await page.getByRole('button',{name:'Save row edits',exact:true}).click();await page.getByText('Spending edits saved locally.',{exact:true}).waitFor();
  await other.locator('#spend-table tbody tr').first().locator('[data-spend-field=category]').fill('Stale change');await other.getByRole('button',{name:'Save row edits',exact:true}).click();await other.getByText('Spending changed in another tab. Reload before saving.',{exact:true}).waitFor();await other.close();
  mkdirSync(join(root,'.artifacts/spending'),{recursive:true});
  for(const width of [1440,768,390,320]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'overflow '+width);await page.screenshot({path:join(root,'.artifacts/spending',`spending-${width}.png`),fullPage:true});}
  await page.getByLabel('Search transactions').fill('Cafe');assert.equal(await page.locator('#spend-table tbody tr').count(),2);await page.getByLabel('Search transactions').fill('');
  page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Delete spending',exact:true}).click();await page.getByText('0 matching · 0 total').waitFor();
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);console.log('Spending browser checks passed: import, review, totals, duplicates, conflicts, export, access control, deletion, responsive layouts and no external requests.');
 }finally{if(browser)await browser.close();try{cli('stop');}catch{}rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
