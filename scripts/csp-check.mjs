export function installCspCapture(){globalThis.__launchCspViolations=[];document.addEventListener('securitypolicyviolation',event=>globalThis.__launchCspViolations.push({directive:event.effectiveDirective,blocked:event.blockedURI}));}
export function readCspViolations(){return globalThis.__launchCspViolations||[];}

export async function loadHtmlCspHeaders(){
 const {readFile}=await import('node:fs/promises');let global=false,policy;
 for(const line of (await readFile('_headers','utf8')).split(/\r?\n/)){
  if(line.trim()&&!/^\s/.test(line)){global=line.trim()==='/*';continue;}
  const match=line.match(/^\s+Content-Security-Policy:\s*(.+)$/i);
  if(global&&match){if(policy)throw Error('Duplicate global CSP in _headers');policy=match[1];}
 }
 if(!policy)throw Error('Global CSP missing from _headers');
 return {'content-security-policy':policy};
}
