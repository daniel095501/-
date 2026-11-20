const path=require('path');
const {chromium}=require(path.join(path.dirname(process.execPath),'../node_modules/playwright'));
const fs=require('fs');
const assert=require('assert/strict');
const base=process.env.TRAVEL_WIKI_URL;
if(!base)throw new Error('TRAVEL_WIKI_URL required');
const out=path.resolve(process.env.TRAVEL_WIKI_QA_DIR||'outputs/travel-wiki-delivery');
fs.mkdirSync(out,{recursive:true});
const passed=[];const ok=s=>passed.push(s);
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  await page.goto(base);
  assert.equal(await page.locator('.wiki-card').count(),6);ok('首頁列出六篇Wiki，資料統計與實際內容相符');
  await page.screenshot({path:path.join(out,'01_Wiki首頁_桌機.png'),fullPage:true});
  await page.getByRole('searchbox').fill('雨量');assert.equal(await page.locator('.wiki-card:visible').count(),1);
  await page.getByRole('searchbox').fill('不存在的測試字串');assert.equal(await page.locator('#wiki-empty').isVisible(),true);
  await page.getByRole('searchbox').fill('');assert.equal(await page.locator('.wiki-card:visible').count(),6);ok('Wiki搜尋與空結果可正常呈現');
  await page.goto(base+'sources.html');assert.equal(await page.locator('.source-card').count(),5);
  assert.match(await page.locator('#S05').textContent(),/2020-03/);assert.match(await page.locator('#S05').textContent(),/題名已核對/);ok('五份來源顯示版本、範圍與PDF題名修正');
  await page.goto(base+'slides.html');
  assert.equal(await page.locator('.slide:visible').count(),1);assert.equal(await page.locator('.slide').count(),14);
  assert.equal(await page.getByRole('button',{name:'上一頁',exact:true}).isDisabled(),true);ok('簡報初始只顯示一頁，並有正確邊界');
  await page.getByRole('button',{name:'下一頁',exact:true}).click();assert.match(page.url(),/#slide-goals$/);
  await page.locator('h2:visible').click();await page.keyboard.press('ArrowRight');assert.match(page.url(),/#slide-case$/);
  await page.locator('h2:visible').click();await page.keyboard.press('Home');assert.match(page.url(),/#slide-start$/);
  await page.keyboard.press('End');assert.match(page.url(),/#slide-finish$/);assert.equal(await page.getByRole('button',{name:'下一頁',exact:true}).isDisabled(),true);ok('按鈕、方向鍵與Home／End翻頁正常');
  await page.getByRole('combobox',{name:'選擇教學頁'}).selectOption('3');assert.match(page.url(),/#slide-method$/);
  await page.locator('h2:visible').click();await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:path.join(out,'02_四格查核教學_桌機.png'),fullPage:true});
  await page.goto(base+'slides.html#slide-practice');assert.equal(await page.locator('.slide:visible').getAttribute('id'),'slide-practice');
  await page.reload();assert.equal(await page.locator('.slide:visible').getAttribute('id'),'slide-practice');ok('選頁與網址定位可直接開啟、重新載入');
  await page.goto(base+'slides.html#unknown');assert.equal(await page.locator('.slide:visible').getAttribute('id'),'slide-start');ok('無效頁碼會回到可閱讀的第一頁');
  for(const [id,correct] of [['case',0],['weather',1],['practice',1]]){
   await page.goto(base+'slides.html#slide-'+id);
   const active=page.locator('.slide:visible');await active.getByRole('button',{name:'確認答案'}).click();
   assert.match(await active.locator('.quiz-feedback').textContent(),/請先選/);
   const wrong=correct===0?1:0;await active.locator('input[type=radio]').nth(wrong).check();await active.getByRole('button',{name:'確認答案'}).click();
   assert.equal(await active.locator('.quiz').getAttribute('data-result'),'retry');
   await active.locator('input[type=radio]').nth(correct).check();await active.getByRole('button',{name:'確認答案'}).click();
   assert.equal(await active.locator('.quiz').getAttribute('data-result'),'correct');
  }ok('三題測驗均檢查未選、錯誤與正確回答');
  const before=page.url();await page.locator('.slide:visible input[type=radio]').first().focus();await page.keyboard.press('ArrowRight');assert.equal(page.url(),before);ok('操作測驗選項時，方向鍵不會誤觸翻頁');
  for(let i=0;i<14;i++){
   await page.getByRole('combobox').selectOption(String(i));
   const active=page.locator('.slide:visible');assert.equal(await active.locator('.slide-evidence').count(),1);
   await active.locator('summary').click();assert.ok(await active.locator('.slide-evidence a[href*="wiki/"]').count()>0);
   await active.locator('summary').click();
  }ok('十四頁各有可開啟的Wiki與來源對應');
  const wiki=['verification-method','preflight-check','airline-conditions','baggage-types','ticket-status','rain-probability'];
  for(const width of [390,320]){
   await page.setViewportSize({width,height:844});
   for(const route of ['index.html','sources.html','workflow.html',...wiki.map(x=>'wiki/'+x+'.html')]){
    await page.goto(base+route);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Overflow ${width} ${route}`);
   }
   await page.goto(base+'slides.html');
   for(let i=0;i<14;i++){
    await page.getByRole('combobox').selectOption(String(i));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Overflow ${width} slide ${i}`);
   }
  }ok('全部網站頁面與十四張簡報在390px、320px無水平溢出');
  await page.setViewportSize({width:390,height:844});await page.goto(base+'slides.html#slide-weather');
  await page.locator('.slide:visible input[type=radio]').nth(1).check();await page.getByRole('button',{name:'確認答案'}).click();
  await page.locator('h2:visible').click();await page.evaluate(()=>scrollTo(0,0));
  const mobileLayout=await page.evaluate(()=>({slide:document.querySelector('.slide:not([hidden])').getBoundingClientRect().bottom,controls:document.querySelector('.deck-controls').getBoundingClientRect().top}));
  assert(mobileLayout.controls>=mobileLayout.slide,'Mobile controls overlap slide content');ok('手機翻頁列排在內容後方，不遮住測驗');
  await page.screenshot({path:path.join(out,'03_天氣測驗_手機.png'),fullPage:true});
  await page.emulateMedia({media:'print'});assert.equal(await page.locator('.slide:visible').count(),14);assert.equal(await page.locator('.deck-controls').isVisible(),false);ok('列印時呈現全部十四頁教學');await page.emulateMedia({media:'screen'});
  const nojs=await browser.newContext({javaScriptEnabled:false});const plain=await nojs.newPage();await plain.goto(base+'slides.html');
  assert.equal(await plain.locator('.slide:visible').count(),14);assert.equal(await plain.locator('.deck-controls').isVisible(),false);assert.equal(await plain.locator('noscript').isVisible(),true);await nojs.close();ok('停用JavaScript仍可讀全部教學內容');
  await page.setViewportSize({width:1440,height:1000});await page.goto(base+'workflow.html');
  assert.equal(await page.locator('.flow-nodes li').count(),6);assert.match(await page.locator('.event-list').textContent(),/題名/);assert.equal(await page.locator('.review-card').count(),2);ok('流程頁保留來源問題、兩次內容修訂與返回路徑');
  assert.deepEqual(errors,[]);ok('沒有JavaScript錯誤或網站HTTP資源錯誤');
  const result={status:'passed',checked_utc:new Date().toISOString(),url:base,browser:'isolated headless Chrome',passed:passed.length,checks:passed,publication_scope:base.startsWith('http://127.')?'本機瀏覽器驗證，尚未代表公開網站':'公開網站驗證'};
  fs.writeFileSync(path.join(out,'browser-qa.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
