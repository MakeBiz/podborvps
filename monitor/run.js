#!/usr/bin/env node
/**
 * Ежедневный сбор цен. Запускается по расписанию, пишет:
 *   data/plans.json      актуальный снимок для сайта
 *   data/history.jsonl   история изменений, из неё делается раздел "изменения цен"
 *   data/status.json     состояние источников для дашборда и алертов
 *
 * Ключевое правило: тариф без свежей проверки НЕ показывается на сайте.
 * Лучше пустая карточка, чем цена месячной давности.
 */
const fs = require('fs');
const path = require('path');
const { normalizePlan } = require('./normalize');
const { comparePlans, sanityCheck } = require('./diff');

const DATA = path.join(__dirname, 'data');
const MAX_AGE_DAYS = 7;          // старше - скрываем с витрины
const TIMEOUT_MS = 20000;
const POLITE_DELAY_MS = 1500;    // пауза между запросами к одному хосту

const NOW = new Date().toISOString().slice(0, 10);
const env = process.env;
const rates = JSON.parse(env.FX_RATES || '{"USD":92,"EUR":100,"AED":25}');

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function fetchJson(url, opts = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      ...opts,
      signal: ctrl.signal,
      headers: { 'User-Agent': 'PodborVPS-PriceMonitor/1.0 (+https://podborvps.ru/methodology)', ...(opts.headers || {}) }
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.json();
  } finally { clearTimeout(t); }
}

function load(file, fallback) {
  try { return JSON.parse(fs.readFileSync(path.join(DATA, file), 'utf8')); }
  catch { return fallback; }
}
function save(file, obj) {
  fs.mkdirSync(DATA, { recursive: true });
  fs.writeFileSync(path.join(DATA, file), JSON.stringify(obj, null, 2) + '\n');
}

async function collect(only) {
  const registry = require('./sources/_registry');
  const prevAll = load('plans.json', []);
  const status = load('status.json', {});
  const result = [];
  const report = [];

  for (const src of registry) {
    if (only && src.slug !== only) continue;
    if (src.kind === 'manual') {
      // ручные источники не трогаем, просто переносим прошлый снимок как есть
      const kept = prevAll.filter(p => p.providerSlug === src.slug);
      result.push(...kept);
      report.push({ slug: src.slug, ok: true, mode: 'manual', count: kept.length });
      continue;
    }

    const prev = prevAll.filter(p => p.providerSlug === src.slug);
    try {
      let raw;
      if (src.kind === 'api') {
        const mod = require('./sources/' + src.slug);
        raw = await mod.fetchPlans({ fetchJson, env });
      } else {
        const parseHtml = require('./html-parser');
        raw = await parseHtml(src.slug, { timeout: TIMEOUT_MS, delay: POLITE_DELAY_MS });
      }
      const plans = raw
        .map(r => normalizePlan({ ...r, source: src.kind, verifiedAt: NOW }, src.slug, rates))
        .filter(Boolean);

      const problems = sanityCheck(src.slug, prev, plans);
      if (problems.length) {
        // данные подозрительные: НЕ подменяем витрину, оставляем прошлые и зовём человека
        result.push(...prev);
        status[src.slug] = { ok: false, lastOk: (status[src.slug] || {}).lastOk || null, problems, checkedAt: NOW };
        report.push({ slug: src.slug, ok: false, problems, count: plans.length });
        continue;
      }

      const changes = comparePlans(prev, plans);
      const total = changes.priceUp.length + changes.priceDown.length + changes.added.length + changes.removed.length;
      if (total) {
        fs.appendFileSync(path.join(DATA, 'history.jsonl'),
          JSON.stringify({ date: NOW, provider: src.slug, changes: {
            priceUp: changes.priceUp.map(c => ({ id: c.plan.id, name: c.plan.name, from: c.from, to: c.to, pct: c.pct })),
            priceDown: changes.priceDown.map(c => ({ id: c.plan.id, name: c.plan.name, from: c.from, to: c.to, pct: c.pct })),
            added: changes.added.map(p => ({ id: p.id, name: p.name, price: p.price })),
            removed: changes.removed.map(p => ({ id: p.id, name: p.name })),
            specChanged: changes.specChanged.map(c => ({ id: c.plan.id, field: c.field, from: c.from, to: c.to }))
          } }) + '\n');
      }

      result.push(...plans);
      status[src.slug] = { ok: true, lastOk: NOW, problems: [], checkedAt: NOW, count: plans.length };
      report.push({ slug: src.slug, ok: true, count: plans.length, changed: total });
    } catch (e) {
      // источник упал: оставляем прошлые данные, они протухнут сами через MAX_AGE_DAYS
      result.push(...prev);
      status[src.slug] = { ok: false, lastOk: (status[src.slug] || {}).lastOk || null, problems: [String(e.message)], checkedAt: NOW };
      report.push({ slug: src.slug, ok: false, problems: [String(e.message)] });
    }
    await sleep(POLITE_DELAY_MS);
  }

  // помечаем протухшие: сайт такие не показывает
  const today = new Date(NOW);
  for (const p of result) {
    const age = (today - new Date(p.verifiedAt)) / 86400000;
    p.stale = age > MAX_AGE_DAYS;
    p.ageDays = Math.round(age);
  }

  save('plans.json', result);
  save('status.json', status);

  const fresh = result.filter(p => !p.stale).length;
  console.log(`\nВсего тарифов: ${result.length}, свежих: ${fresh} (${Math.round(fresh / (result.length || 1) * 100)}%)`);
  console.table(report);
  const broken = report.filter(r => !r.ok);
  if (broken.length) {
    console.error('\nПРОБЛЕМНЫЕ ИСТОЧНИКИ:');
    broken.forEach(b => console.error(' ', b.slug, b.problems.join('; ')));
    process.exitCode = 1;   // CI подсветит красным, придёт уведомление
  }
  return result;
}

if (require.main === module) {
  const only = process.argv[2] || null;
  collect(only).catch(e => { console.error('фатально:', e); process.exit(1); });
}
module.exports = { collect };
