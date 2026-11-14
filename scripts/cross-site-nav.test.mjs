import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
const source = readFileSync(new URL('../cross-site-nav.js', import.meta.url), 'utf8');
function render(hostname, pathname) {
 const elements=[];
 const createElement=tag=>{const element={tag,attrs:{},children:[],style:{},setAttribute(k,v){this.attrs[k]=v;},appendChild(c){this.children.push(c);},append(...children){this.children.push(...children);},addEventListener(){}};elements.push(element);return element;};
 const body=createElement('body');
 const context=vm.createContext({URL,window:{location:{hostname,pathname},matchMedia:()=>({matches:false})},document:{body,createElement,querySelector:()=>body.children.find(e=>'data-estate-navigation' in e.attrs),documentElement:{getAttribute:()=>null}},getComputedStyle:()=>({backgroundColor:'rgb(255,255,255)'})});
 vm.runInContext(source,context);vm.runInContext(source,context);
 return {body,links:elements.filter(e=>e.tag==='a')};
}
for(const [host,path,self] of [['axylusion.com','/gallery.html','https://axylusion.com'],['www.axylusion.com','/','https://axylusion.com'],['koltregaskes.github.io','/ai-resource-hub/news/','https://theairesourcehub.com'],['koltregaskes.github.io','/synthetic-thoughts/','https://ghostinthemodels.com']]) {
 test(`${host}${path} excludes self and inserts once`,()=>{
  const {body,links}=render(host,path);
  assert.equal(body.children.length,1);
  assert.equal(links.length,4);
  assert.ok(!links.some(l=>l.href===self));
  assert.ok(links.every(l=>l.style.cssText.includes('min-height: 24px')&&l.style.cssText.includes('opacity: 1;')&&l.style.cssText.includes('text-decoration: underline')));
  assert.equal(body.children[0].children[0].attrs['aria-label'],'Other sites by Kol Tregaskes');
 });
}
