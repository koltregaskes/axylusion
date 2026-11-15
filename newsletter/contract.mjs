/** Offline backend contract. No HTTP server, environment lookup or network I/O. */
import {createHmac, randomUUID, timingSafeEqual} from 'node:crypto';
import {readFileSync} from 'node:fs';

const mapping = JSON.parse(readFileSync(new URL('./categories.json', import.meta.url), 'utf8'));
export const categories = Object.freeze(mapping.categories);
const escape = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
const clone = value => structuredClone(value);
const consentPolicy = JSON.parse(readFileSync(new URL('./consent.json', import.meta.url), 'utf8'));
export const consentSources = Object.freeze(consentPolicy.allowedSources);
const consentVersion = consentPolicy.consentVersion;

function validatedConsentSource(value) {
  if (typeof value !== 'string' || !consentSources.includes(value)) throw Error('Allowlisted consent source required');
  return value;
}

function preferences(values) {
  if (!Array.isArray(values) || !values.length || values.some(value => !categories.includes(value))) {
    throw Error('Choose at least one valid category');
  }
  return categories.filter(value => values.includes(value));
}
function emailAddress(value) {
  if (typeof value !== 'string' || value.length > 254 || !/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/.test(value)) {
    throw Error('Invalid email address');
  }
  return value.toLowerCase();
}
function httpsBase(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) throw Error('HTTPS backend base required');
  return url.href.replace(/\/$/, '');
}
function isoDay(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value) {
    throw Error('Invalid source or edition date');
  }
  return value;
}
function fresh(sourceDate, editionDate) {
  if (!sourceDate) return false;
  const age = Date.parse(isoDay(editionDate)) - Date.parse(isoDay(sourceDate));
  return age >= 0 && age <= 86400000;
}

/** Renders only fresh stories in confirmed preferences, with an edition backlink.
 * An empty preference match is an explicit skip, never a successful delivery.
 */
export function renderEdition(edition, chosenCategories) {
  const chosen = preferences(chosenCategories);
  const day = isoDay(edition.date);
  const editionUrl = `https://axylusion.com/editions/${day}.html`;
  if (edition.url !== editionUrl || !Array.isArray(edition.items)) throw Error('Invalid dated edition');
  for (const item of edition.items) {
    if (!categories.includes(item.category)) throw Error('Unknown edition category');
    const url = new URL(item.url);
    if (url.protocol !== 'https:' || url.username || url.password) throw Error('Unsafe story URL');
    if (item.sourceDate) isoDay(item.sourceDate);
  }
  const items = edition.items.filter(item => chosen.includes(item.category) && fresh(item.sourceDate, day));
  if (!items.length) return {status:'skipped', reason:'No fresh items in chosen categories', editionUrl};
  const sections = chosen.map(category => {
    const matches = items.filter(item => item.category === category);
    return `<h2>${category}</h2>` + (matches.length ? '<ul>' + matches.map(item => `<li><a href="${escape(item.url)}">${escape(item.title)}</a> · ${escape(item.source)} · Source date: ${escape(item.sourceDate)}</li>`).join('') + '</ul>' : '<p>No fresh items in this category for this edition.</p>');
  });
  return {status:'rendered', subject:`Axy Lusion creative edition: ${day}`, editionUrl,
    html:`<html lang="en-GB"><body><h1>Axy Lusion creative edition: ${day}</h1><p><a href="${editionUrl}">Read the dated edition</a></p>${sections.join('')}</body></html>`,
    text:[`Axy Lusion creative edition: ${day}`, `Read the dated edition: ${editionUrl}`,
      ...chosen.flatMap(category => [category, ...items.filter(item => item.category === category).map(item => `${item.title} | ${item.source} | Source date: ${item.sourceDate} | ${item.url}`),
        ...(items.some(item => item.category === category) ? [] : ['No fresh items in this category for this edition.'])])].join('\n')};
}

/** A future sender must implement async send(message) and return a receipt.
 * This fake stores messages in memory only; its receipts never mean delivered.
 */
export class MemoryTransport {
  messages = [];
  async send(message) {
    this.messages.push(clone(message));
    return {status:'captured', id:`memory-${this.messages.length}`};
  }
}

/** Resend is selected, but this intentionally cannot send even with a key.
 * Runtime injection is the only future configuration path; no SDK or fetch.
 */
export class ResendTransport {
  #apiKey;
  constructor({apiKey} = {}) { this.#apiKey = apiKey; }
  async send() {
    if (!this.#apiKey) throw Error('not configured');
    throw Error('Resend adapter stub: live sending is not implemented');
  }
}

export class NewsletterContract {
  #records = new Map();
  #sent = new Set();
  #busy = new Set();
  #key;
  #clock;
  #transport;
  #base;
  constructor({tokenKey, clock, transport, backendBase}) {
    if (!(tokenKey instanceof Uint8Array) || tokenKey.length < 32) throw Error('Inject at least 32 bytes of signing key at runtime');
    if (typeof clock !== 'function' || typeof transport?.send !== 'function') throw Error('Clock and sender interface required');
    this.#key = Buffer.from(tokenKey);
    this.#clock = clock;
    this.#transport = transport;
    this.#base = httpsBase(backendBase);
  }
  #now() {
    const now = this.#clock();
    if (!(now instanceof Date) || !Number.isFinite(now.getTime())) throw Error('Invalid clock');
    return now;
  }
  #sign(body) { return createHmac('sha256', this.#key).update(body).digest('base64url'); }
  #token(record, purpose, seconds) {
    const payload = {id:record.id, purpose, version:record.subscriptionVersion,
      expires:seconds === null ? null : this.#now().getTime() + seconds * 1000};
    const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
    return body + '.' + this.#sign(body);
  }
  #read(token, purpose) {
    if (typeof token !== 'string' || token.length > 2048 || !/^[\w-]+\.[\w-]+$/.test(token)) throw Error('Invalid token');
    const [body, signature] = token.split('.');
    const expected = Buffer.from(this.#sign(body));
    const supplied = Buffer.from(signature);
    if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) throw Error('Invalid token');
    const data = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    const record = this.#records.get(data.id);
    if (!record || data.purpose !== purpose || data.version !== record.subscriptionVersion ||
        (data.expires !== null && (!Number.isFinite(data.expires) || this.#now().getTime() >= data.expires))) throw Error('Invalid or expired token');
    return record;
  }
  /** Minimal record: id, email, categories, consentAt/version/source, status,
   * confirmedAt, preferencesUpdatedAt, unsubscribedAt, subscriptionVersion.
   * Explicit consent is required. Re-registering never overwrites an owner.
   */
  subscribe({email, categories: chosen, consent, consentSource}) {
    if (consent !== true) throw Error('Explicit consent required');
    const source = validatedConsentSource(consentSource);
    const address = emailAddress(email), selected = preferences(chosen);
    if ([...this.#records.values()].some(record => record.email === address)) throw Error('Subscription already recorded');
    const record = {id:randomUUID(), email:address, categories:selected, consentAt:this.#now().toISOString(), consentVersion, consentSource:source,
      confirmedAt:null, preferencesUpdatedAt:null, unsubscribedAt:null, status:'pending', subscriptionVersion:1};
    this.#records.set(record.id, record);
    const token = this.#token(record, 'confirm', 86400);
    return {record:clone(record), confirmationToken:token, confirmationUrl:`${this.#base}/confirm?token=${token}`};
  }
  /** Internal persistence snapshot, never an unauthenticated HTTP response. */
  record(id) {
    const record = this.#records.get(id);
    return record ? clone(record) : null;
  }
  /** A future backend must send the confirmation email through the sender.
   * GET only previews confirmation; an explicit POST should call this method.
   */
  confirm(token) {
    const record = this.#read(token, 'confirm');
    if (record.status !== 'pending') throw Error('Confirmation already used or subscription stopped');
    record.status = 'confirmed'; record.confirmedAt = this.#now().toISOString();
    return clone(record);
  }
  links(id) {
    const record = this.#records.get(id);
    if (record?.status !== 'confirmed') throw Error('Confirmed subscription required');
    const preferencesToken = this.#token(record, 'preferences', 3600);
    const unsubscribeToken = this.#token(record, 'unsubscribe', null);
    return {preferencesToken, unsubscribeToken,
      preferencesUrl:`${this.#base}/preferences?token=${preferencesToken}`,
      unsubscribeUrl:`${this.#base}/unsubscribe?token=${unsubscribeToken}`};
  }
  updatePreferences(token, chosen) {
    const record = this.#read(token, 'preferences');
    if (record.status !== 'confirmed') throw Error('Confirmed subscription required');
    record.categories = preferences(chosen);
    record.preferencesUpdatedAt = this.#now().toISOString();
    return clone(record);
  }
  /** RFC 8058 endpoint contract: GET never mutates; signed POST needs no login.
   * Unsubscribe tokens remain valid after preference updates and repeated POSTs.
   */
  oneClick({token, method, contentType = '', body = ''}) {
    const record = this.#read(token, 'unsubscribe');
    if (method === 'GET') return {status:200, changed:false, message:'Confirm unsubscribe with POST'};
    const params = new URLSearchParams(body);
    if (method !== 'POST' || contentType.split(';')[0].trim().toLowerCase() !== 'application/x-www-form-urlencoded' ||
        [...params].length !== 1 || params.get('List-Unsubscribe') !== 'One-Click') throw Error('Valid one-click POST required');
    const changed = record.status !== 'unsubscribed';
    if (changed) {
      record.status = 'unsubscribed'; record.unsubscribedAt = this.#now().toISOString();
    }
    return {status:200, changed};
  }
  async sendEdition(id, edition) {
    const record = this.#records.get(id);
    if (record?.status !== 'confirmed') throw Error('Confirmed subscription required');
    if (edition.date !== this.#now().toISOString().slice(0,10)) return {status:'skipped', reason:'Edition is not for today (UTC)'};
    const rendered = renderEdition(edition, record.categories);
    if (rendered.status === 'skipped') return rendered;
    const key = id + ':' + edition.date;
    if (this.#sent.has(key)) return {status:'skipped', reason:'Edition already captured'};
    if (this.#busy.has(key)) throw Error('Edition send already in progress');
    const links = this.links(id);
    const message = {to:record.email, subject:rendered.subject,
      html:rendered.html.replace('</body>', `<p><a href="${escape(links.preferencesUrl)}">Change categories</a> · <a href="${escape(links.unsubscribeUrl)}">Unsubscribe</a></p></body>`),
      text:rendered.text + `\nChange categories: ${links.preferencesUrl}\nUnsubscribe: ${links.unsubscribeUrl}`,
      headers:{'List-Unsubscribe':`<${links.unsubscribeUrl}>`, 'List-Unsubscribe-Post':'List-Unsubscribe=One-Click'},
      idempotencyKey:key};
    this.#busy.add(key);
    try {
      const receipt = await this.#transport.send(message);
      if (!receipt?.id || receipt.status !== 'captured') throw Error('Sender did not return a fake capture receipt');
      this.#sent.add(key);
      return {...receipt, delivered:false};
    } finally { this.#busy.delete(key); }
  }
}
