export function installCspCapture(){globalThis.__launchCspViolations=[];document.addEventListener('securitypolicyviolation',event=>globalThis.__launchCspViolations.push({directive:event.effectiveDirective,blocked:event.blockedURI}));}
export function readCspViolations(){return globalThis.__launchCspViolations||[];}

export async function loadHtmlCspHeaders(){
 const {readFile}=await import('node:fs/promises');
 const payload=JSON.parse(await readFile(new URL('../cloudflare-response-headers.json',import.meta.url),'utf8'));
 if(payload.rules?.length!==1)throw Error('Expected one proposed Cloudflare rule');
 const entry=payload.rules[0].action_parameters?.headers?.['Content-Security-Policy'];
 const policy=entry?.value;
 if(entry?.operation!=='set'||!policy)throw Error('Enforced CSP missing from Cloudflare proposal');
 return {'content-security-policy':policy};
}
