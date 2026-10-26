import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'

function createElement(tag) {
  const element = {
    tagName: String(tag || 'div').toUpperCase(),
    children: [],
    parent: null,
    className: '',
    dataset: {},
    classList: {
      values: new Set(),
      toggle(name, force) {
        const on = force === undefined ? !this.values.has(name) : Boolean(force)
        if (on) this.values.add(name)
        else this.values.delete(name)
        return on
      },
      add(name) { this.values.add(name) },
      contains(name) { return this.values.has(name) },
    },
    attributes: {},
    listeners: {},
    innerHTML: '',
    setAttribute(name, value) { this.attributes[name] = String(value) },
    getAttribute(name) { return this.attributes[name] },
    addEventListener(type, handler) { this.listeners[type] = handler },
    appendChild(child) {
      if (child.parent) child.parent.children = child.parent.children.filter((item) => item !== child)
      child.parent = this
      this.children.push(child)
      return child
    },
    querySelector(selector) {
      return this.querySelectorAll(selector)[0] || null
    },
    querySelectorAll(selector) {
      const found = []
      const visit = (node) => {
        if (node !== this && matches(node, selector)) found.push(node)
        for (const child of node.children || []) visit(child)
      }
      visit(this)
      return found
    },
  }
  Object.defineProperty(element, 'innerHTML', {
    get() { return element._html || '' },
    set(value) {
      element._html = String(value)
      element.children = []
      for (const match of String(value).matchAll(/<li data-topic="([^"]*)">/g)) {
        const item = createElement('li')
        item.dataset.topic = match[1]
        element.appendChild(item)
      }
    },
  })
  return element
}

function matches(element, selector) {
  if (selector === '[data-digest-date]') return Boolean(element.dataset.digestDate)
  if (selector === '[data-news-list]') return element.dataset.newsList === '1'
  if (selector === '.cn-digests__head') return element.classList.contains('cn-digests__head')
  if (selector === '[data-news-search]') return element.dataset.newsSearch === '1'
  if (selector === '[data-news-range]') return Boolean(element.dataset.newsRange)
  if (selector === '[data-news-topic]') return Boolean(element.dataset.newsTopic)
  if (selector === '[data-news-clear], [data-news-empty-reset]') return element.dataset.newsClear === '1'
  if (selector === '[data-news-empty]') return element.dataset.newsEmpty === '1'
  if (selector === 'li[data-topic]') return element.tagName === 'LI' && Boolean(element.dataset.topic)
  return false
}

function digestRow(day, title) {
  const row = createElement('article')
  row.dataset.digestDate = day
  row.dataset.digestSearch = title.toLowerCase()
  const item = createElement('li')
  item.dataset.topic = 'Tools'
  row.appendChild(item)
  return row
}

async function page(feed) {
  const list = createElement('section')
  list.dataset.newsList = '1'
  const head = createElement('div')
  head.classList.add('cn-digests__head')
  list.appendChild(head)
  list.appendChild(digestRow('2026-10-25', 'Newer archive story'))
  list.appendChild(digestRow('2026-10-24', 'Older archive story'))
  const search = createElement('input')
  search.dataset.newsSearch = '1'
  const day = createElement('button')
  day.dataset.newsRange = 'day'
  const week = createElement('button')
  week.dataset.newsRange = 'week'
  const all = createElement('button')
  all.dataset.newsRange = 'all'
  const topic = createElement('button')
  topic.dataset.newsTopic = 'All'
  const empty = createElement('p')
  empty.dataset.newsEmpty = '1'
  const document = {
    listeners: {},
    addEventListener(type, handler) { this.listeners[type] = handler },
    createElement,
    querySelector(selector) {
      return [list, search, empty].find((element) => matches(element, selector))
        || list.querySelector(selector)
    },
    querySelectorAll(selector) {
      return [list, search, day, week, all, topic, empty]
        .filter((element) => matches(element, selector))
        .concat(list.querySelectorAll(selector))
    },
  }
  const context = {
    document,
    console,
    fetch: async () => ({
      ok: true,
      json: async () => feed,
    }),
    URL,
    setTimeout,
  }
  context.window = context
  vm.runInNewContext(
    fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'cinematic.js'), 'utf8'),
    context,
  )
  document.listeners.DOMContentLoaded()
  for (let step = 0; step < 10; step += 1) await Promise.resolve()
  return { list, day }
}

test('routed rows join the archive in date order and the newest row anchors the filter', async () => {
  const { list, day } = await page({
    site: 'Axy Lusion',
    articles: [{
      title: 'Older routed story',
      url: 'https://example.com/older-routed',
      date: '2026-10-23T12:00:00.000Z',
      tags: ['product_launch'],
    }],
  })
  const dates = list.querySelectorAll('[data-digest-date]').map((row) => row.dataset.digestDate)
  assert.deepEqual(dates, ['2026-10-25', '2026-10-24', '2026-10-23'])

  day.listeners.click()
  const visible = list.querySelectorAll('[data-digest-date]')
    .filter((row) => !row.classList.contains('is-hidden'))
    .map((row) => row.dataset.digestDate)
  assert.deepEqual(visible, ['2026-10-25'])
})

test('a newer routed row becomes the filter anchor instead of the first archive row', async () => {
  const { list, day } = await page({
    site: 'Axy Lusion',
    articles: [{
      title: 'Newer routed story',
      url: 'https://example.com/newer-routed',
      date: '2026-10-26T12:00:00.000Z',
      tags: ['product_launch'],
    }],
  })
  const dates = list.querySelectorAll('[data-digest-date]').map((row) => row.dataset.digestDate)
  assert.deepEqual(dates, ['2026-10-26', '2026-10-25', '2026-10-24'])

  day.listeners.click()
  const visible = list.querySelectorAll('[data-digest-date]')
    .filter((row) => !row.classList.contains('is-hidden'))
    .map((row) => row.dataset.digestDate)
  assert.deepEqual(visible, ['2026-10-26'])
})
