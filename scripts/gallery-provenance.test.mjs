import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

test('selecting each hero image updates its visible credit with its image and date', () => {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  const decoded = html.match(/data-hero-items='([^']+)'/)[1]
    .replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  const items = JSON.parse(decoded);
  const nodes = Object.fromEntries(['bg', 'ref', 'date', 'prompt', 'credit'].map(key => [key, {
    textContent: '', setAttribute(name, value) { this[name] = value; },
  }]));
  const buttons = items.map((_, index) => ({
    dataset: {heroIndex: String(index)}, classList: {toggle() {}},
    addEventListener(name, callback) { this[name] = callback; },
  }));
  const strip = {getAttribute() { return JSON.stringify(items); }, querySelectorAll() { return buttons; }};
  const document = {
    querySelector(selector) {
      if (selector === '[data-hero-strip]') return strip;
      return nodes[selector.match(/^\[data-hero-(\w+)\]$/)?.[1]] || null;
    },
    querySelectorAll() { return []; },
    addEventListener(name, callback) { if (name === 'DOMContentLoaded') callback(); },
  };
  runInNewContext(readFileSync(new URL('./cinematic.js', import.meta.url), 'utf8'), {document});
  buttons.forEach((button, index) => {
    button.click();
    assert.equal(nodes.bg.style, items[index].style);
    assert.equal(nodes.date.textContent, items[index].date);
    assert.equal(nodes.credit.textContent, items[index].credit);
    assert.match(nodes.credit.textContent, /Kol Tregaskes .* Midjourney v\d .* AI-generated/);
  });
});
