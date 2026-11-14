// Evaluate in the page. Exceptions are explicit reviewed selectors, never a
// blanket allowance for overflow:hidden/clip (including main/html/body).
export function findOverflow({scrollers=[],decorativeClippers=[]}={}) {
 const issues=[],viewport=innerWidth,tolerance=1;
 for(const element of document.querySelectorAll('body *')){
  const rect=element.getBoundingClientRect(),style=getComputedStyle(element);
  if(!rect.width||!rect.height||!element.getClientRects().length)continue;
  // Standard one-pixel clipped accessible labels have no visible text.
  if(rect.width<=1&&rect.height<=1&&style.position==='absolute'&&style.clip!=='auto')continue;
  let hidden=false,reviewed=false,clipper=null;
  for(let ancestor=element;ancestor;ancestor=ancestor.parentElement){
   const computed=getComputedStyle(ancestor),bounds=ancestor.getBoundingClientRect();
   if(computed.display==='none'||computed.visibility==='hidden'||computed.visibility==='collapse'||Number(computed.opacity)===0){hidden=true;break;}
   if(ancestor===element)continue;
   const bounded=bounds.width>0&&bounds.left>=-tolerance&&bounds.right<=viewport+tolerance;
   const root=ancestor===document.body||ancestor===document.documentElement;
   if(!root&&bounded&&((['auto','scroll'].includes(computed.overflowX)&&scrollers.some(selector=>ancestor.matches(selector)))||(['hidden','clip'].includes(computed.overflowX)&&decorativeClippers.some(selector=>ancestor.matches(selector)))))reviewed=true;
   if(['hidden','clip'].includes(computed.overflowX)&&(rect.left<bounds.left-tolerance||rect.right>bounds.right+tolerance))clipper=ancestor.tagName+(ancestor.id?'#'+ancestor.id:'');
  }
  if(hidden||reviewed)continue;
  const viewportOverflow=rect.left < -tolerance||rect.right > viewport+tolerance;
  const containsText=[...element.childNodes].some(node=>node.nodeType===Node.TEXT_NODE&&node.textContent.trim());
  const textContainer=containsText||/^(H[1-6]|P|A|SPAN|STRONG|SMALL|LABEL|CODE|PRE|BUTTON|TD|TH)$/.test(element.tagName);
  let textOverflow=false;
  if(textContainer){const range=document.createRange();range.selectNodeContents(element);textOverflow=[...range.getClientRects()].some(bounds=>bounds.width>0&&(bounds.left<rect.left-tolerance||bounds.right>rect.right+tolerance));}

  if(viewportOverflow||clipper||textOverflow)issues.push({tag:element.tagName,id:element.id,classes:element.getAttribute('class'),left:rect.left,right:rect.right,width:rect.width,clipper,textOverflow});
 }
 return issues;
}
