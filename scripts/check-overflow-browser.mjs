import {chromium} from 'playwright';import assert from 'node:assert/strict';import {findOverflow} from './overflow-check.mjs';
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge'}),errors=[];let count=0;
try{for(const width of [320,390]){const page=await browser.newPage({viewport:{width,height:900}});for(const [name,body,expected,options]of[
 ['main clips 900px','<main style="overflow-x:clip"><div style="width:900px;height:20px">Content</div></main>',true,{}],
 ['transparent wrapper still widens the page','<style>html,body{overflow-x:visible}</style><div style="opacity:0"><div style="width:600px;height:20px">Invisible layout</div></div>',true,{}],
 ['root clips 900px','<style>html,body{overflow-x:hidden}</style><div style="width:900px;height:20px">Content</div>',true,{}],
 ['unreviewed small clip','<div style="width:100px;overflow:hidden"><div style="width:250px;height:20px">Content</div></div>',true,{}],
 ['visible text exceeds its box','<div style="width:100px;white-space:nowrap;overflow-x:visible">WWWWWWWWWWWWWWWWWW</div>',true,{}],
 ['text clipped by its own box','<div style="width:100px;height:20px;white-space:nowrap;overflow:hidden">WWWWWWWWWWWWWWWWWW</div>',true,{}],
 ['visible component overhang stays inside viewport','<main style="width:100px"><div style="width:150px;height:20px">Readable</div></main>',false,{}],
 ['390-only overflow','<style>.only390{width:100px}@media(min-width:380px) and (max-width:400px){.only390{width:900px}}</style><main style="overflow-x:clip"><div class="only390">Content</div></main>',width===390,{}],
 ['reviewed scroller','<div id="reviewed-scroll" style="width:100px;overflow-x:auto"><div style="width:900px;height:20px">Scrollable</div></div>',false,{scrollers:['#reviewed-scroll']}],
 ['reviewed decoration','<div id="reviewed-decoration" style="width:100px;overflow:hidden"><div style="width:900px;height:20px">Decoration</div></div>',false,{decorativeClippers:['#reviewed-decoration']}]
 ]){await page.setContent('<style>html,body{margin:0;width:100%}</style>'+body);const found=await page.evaluate(findOverflow,options);const overflow=found.length>0||await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow!==expected)errors.push(name+' at '+width+'px expected overflow='+expected+' got '+JSON.stringify(found));count++;}await page.close();}assert.deepEqual(errors,[]);console.log('Overflow controls: '+count+' planted phone cases passed');}finally{await browser.close();}
