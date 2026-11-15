import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {categories, NewsletterContract, MemoryTransport, ResendTransport, renderEdition} from './contract.mjs';

// Synthetic fixtures, never credentials or environment lookups.
function setup(transport = new MemoryTransport()) {
  let now = new Date('2026-11-15T15:00:00Z');
  const service = new NewsletterContract({tokenKey:new Uint8Array(32).fill(7), clock:() => now,
    transport, backendBase:'https://backend.example.invalid'});
  const request = (chosen = ['Audio']) => service.subscribe({email:'reader@example.invalid', categories:chosen, consent:true});
  return {service, transport, request, advance:ms => {now = new Date(now.getTime() + ms);}};
}
const edition = {date:'2026-11-15', url:'https://axylusion.com/editions/2026-11-15.html',
  items:categories.map((category,index) => ({category, title:`Story ${category}`, source:'Fixture source',
    sourceDate:'2026-11-14', url:`https://source.example.invalid/${index}`}))};
const post = token => ({token, method:'POST', contentType:'application/x-www-form-urlencoded', body:'List-Unsubscribe=One-Click'});

test('explicit consent, valid address and at least one known category are mandatory', () => {
  const {service, transport} = setup();
  for (const consent of [false, undefined, 'true', 1]) assert.throws(() => service.subscribe({email:'a@example.invalid',categories:['Audio'],consent}), /consent/);
  for (const email of ['bad', 'a@example.invalid\r\nBcc:x@y.invalid', '<a@example.invalid>']) assert.throws(() => service.subscribe({email,categories:['Audio'],consent:true}), /email/);
  for (const chosen of [[], ['Unknown'], 'Audio']) assert.throws(() => service.subscribe({email:'a@example.invalid',categories:chosen,consent:true}), /category/);
  assert.equal(transport.messages.length,0);
});
test('pending records capture consent and cannot receive editions or management links', async () => {
  const {service, request, transport} = setup(); const pending = request();
  assert.equal(pending.record.consentAt,'2026-11-15T15:00:00.000Z');
  assert.equal(pending.record.consentVersion,'creative-daily-v1');
  assert.equal(pending.record.status,'pending'); assert.equal(pending.record.confirmedAt,null);
  await assert.rejects(service.sendEdition(pending.record.id,edition), /Confirmed/);
  assert.throws(() => service.links(pending.record.id), /Confirmed/);
  assert.equal(transport.messages.length,0);
});
test('double opt-in is single use and records confirmation time; repeat signup cannot change an owner', () => {
  const {service, request, advance} = setup(); const pending = request(); advance(1000);
  const confirmed = service.confirm(pending.confirmationToken);
  assert.equal(confirmed.confirmedAt,'2026-11-15T15:00:01.000Z');
  assert.throws(() => service.confirm(pending.confirmationToken), /already/);
  assert.throws(() => request(['Video']), /already/);
  pending.record.categories.push('Video'); assert.deepEqual(confirmed.categories,['Audio']);
});
test('confirmation expires at 24 hours and preference tokens expire at one hour', () => {
  const a = setup(); const pending = a.request(); a.advance(86400000);
  assert.throws(() => a.service.confirm(pending.confirmationToken), /expired/);
  const b = setup(); const p = b.request(); b.service.confirm(p.confirmationToken);
  const links = b.service.links(p.record.id); b.advance(3600000);
  assert.throws(() => b.service.updatePreferences(links.preferencesToken,['Video']), /expired/);
});
test('payload/signature tampering, wrong signing keys and token purpose substitution fail', () => {
  const {service, request} = setup(); const pending = request();
  const [body,sig] = pending.confirmationToken.split('.');
  const data = JSON.parse(Buffer.from(body,'base64url')); data.purpose='unsubscribe';
  const tampered = Buffer.from(JSON.stringify(data)).toString('base64url') + '.' + sig;
  for (const token of [tampered,body+'.'+(sig[0]==='x'?'y':'x')+sig.slice(1), pending.confirmationToken+'.extra', '']) assert.throws(() => service.confirm(token), /token/);
  service.confirm(pending.confirmationToken); const links = service.links(pending.record.id);
  assert.throws(() => service.updatePreferences(links.unsubscribeToken,['Video']), /token/);
  assert.throws(() => service.oneClick(post(links.preferencesToken)), /token/);
  const other = new NewsletterContract({tokenKey:new Uint8Array(32).fill(8), clock:()=>new Date('2026-11-15Z'), transport:new MemoryTransport(), backendBase:'https://backend.example.invalid'});
  assert.throws(() => other.confirm(pending.confirmationToken), /token/);
});
test('saved preferences filter the next email and invalid changes leave the current choice intact', async () => {
  const {service, request, transport} = setup(); const p = request(); service.confirm(p.confirmationToken);
  const links = service.links(p.record.id);
  const record = service.updatePreferences(links.preferencesToken,['Video','Video']);
  assert.deepEqual(record.categories,['Video']); assert.ok(record.preferencesUpdatedAt);
  assert.throws(() => service.updatePreferences(links.preferencesToken,[]), /category/);
  await service.sendEdition(p.record.id,edition);
  assert.match(transport.messages[0].html,/Story Video/); assert.doesNotMatch(transport.messages[0].html,/Story Audio|Story Visuals|Story Workflows/);
});
test('RFC 8058 headers and signed one-click POST stop subsequent sends; GET and invalid POST never unsubscribe', async () => {
  const {service, request, transport} = setup(); const p = request(); service.confirm(p.confirmationToken);
  const links = service.links(p.record.id);
  assert.equal(service.oneClick({token:links.unsubscribeToken,method:'GET'}).changed,false);
  for (const request of [{...post(links.unsubscribeToken),method:'PUT'}, {...post(links.unsubscribeToken),body:''}, {...post(links.unsubscribeToken),contentType:'text/plain'}, {...post(links.unsubscribeToken),body:'List-Unsubscribe=One-Click&extra=1'}]) assert.throws(()=>service.oneClick(request), /POST/);
  const receipt = await service.sendEdition(p.record.id,edition);
  assert.deepEqual(receipt,{status:'captured',id:'memory-1',delivered:false});
  const message = transport.messages[0];
  assert.equal(message.headers['List-Unsubscribe'],`<${links.unsubscribeUrl}>`);
  assert.equal(message.headers['List-Unsubscribe-Post'],'List-Unsubscribe=One-Click');
  assert.match(message.html,/Change categories/); assert.match(message.text,/Unsubscribe: https:/);
  service.updatePreferences(links.preferencesToken,['Video']);
  assert.equal(service.oneClick(post(links.unsubscribeToken)).changed,true);
  assert.equal(service.oneClick(post(links.unsubscribeToken)).changed,false);
  await assert.rejects(service.sendEdition(p.record.id,edition), /Confirmed/);
  assert.throws(() => service.updatePreferences(links.preferencesToken,['Audio']), /Confirmed/);
  assert.equal(transport.messages.length,1);
});
test('freshness excludes old, unknown and future source dates and stale editions', async () => {
  const {service, request, transport} = setup(); const p=request(); service.confirm(p.confirmationToken);
  for (const sourceDate of ['2026-11-13',null,'2026-11-16']) {
    assert.equal((await service.sendEdition(p.record.id,{...edition,items:[{...edition.items[2],sourceDate}]})).status,'skipped');
  }
  assert.equal((await service.sendEdition(p.record.id,{...edition,date:'2026-11-14',url:'https://axylusion.com/editions/2026-11-14.html'})).status,'skipped');
  assert.equal(transport.messages.length,0);
});
test('email escapes source text, rejects unsafe URLs and links back to its exact dated page', () => {
  const rendered=renderEdition({...edition,items:[{...edition.items[2],title:'<script>bad</script> & "quote"'}]},['Audio']);
  assert.match(rendered.html,/&lt;script&gt;/); assert.doesNotMatch(rendered.html,/<script>/);
  assert.ok(rendered.html.includes(`href="${edition.url}"`)); assert.ok(rendered.text.includes(edition.url));
  assert.throws(()=>renderEdition({...edition,url:'https://wrong.example.invalid'},['Audio']), /dated edition/);
  assert.throws(()=>renderEdition({...edition,items:[{...edition.items[2],url:'javascript:alert(1)'}]},['Audio']), /Unsafe/);
  assert.throws(()=>renderEdition({...edition,date:'2026-02-30'},['Audio']), /date/);
});
test('fake delivery failure is explicit and retryable; duplicate captures are skipped', async () => {
  const memory=new MemoryTransport(); let fail=true;
  const {service,request}=setup({send:message=>{if(fail)throw Error('fixture transport failure');return memory.send(message);}});
  const p=request(); service.confirm(p.confirmationToken);
  await assert.rejects(service.sendEdition(p.record.id,edition),/transport failure/); assert.equal(memory.messages.length,0);
  fail=false; assert.equal((await service.sendEdition(p.record.id,edition)).status,'captured');
  assert.equal((await service.sendEdition(p.record.id,edition)).status,'skipped'); assert.equal(memory.messages.length,1);
});
test('concurrent capture cannot produce duplicate messages', async () => {
  let release; const waiting=new Promise(resolve=>{release=resolve;}); const memory=new MemoryTransport();
  const {service,request}=setup({send:async message=>{await waiting; return memory.send(message);}});
  const p=request(); service.confirm(p.confirmationToken); const first=service.sendEdition(p.record.id,edition);
  await assert.rejects(service.sendEdition(p.record.id,edition),/in progress/); release(); await first;
  assert.equal(memory.messages.length,1);
});
test('unconfigured and runtime-injected Resend stub cannot call the network', async () => {
  await assert.rejects(new ResendTransport().send({}), /^Error: not configured$/);
  await assert.rejects(new ResendTransport({apiKey:'synthetic-fixture'}).send({}), /not implemented/);
  assert.throws(()=>new NewsletterContract({tokenKey:new Uint8Array(1)}), /32 bytes/);
});
test('real generated editions render into emails with their dated edition backlinks', () => {
  const {editions}=JSON.parse(readFileSync(new URL('../data/newsletter-editions.json',import.meta.url),'utf8'));
  let count=0;
  for (const entry of editions) {
    const rendered=renderEdition(entry,categories);
    if (rendered.status==='skipped')continue;
    count++; assert.ok(rendered.html.includes(`href="${entry.url}"`)); assert.ok(rendered.text.includes(entry.url));
  }
  assert.ok(count>0,'Actual supplied sources must render, not just synthetic fixtures');
});
