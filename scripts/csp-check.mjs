export function installCspCapture(){globalThis.__launchCspViolations=[];document.addEventListener('securitypolicyviolation',event=>globalThis.__launchCspViolations.push({directive:event.effectiveDirective,blocked:event.blockedURI}));}
export function readCspViolations(){return globalThis.__launchCspViolations||[];}
