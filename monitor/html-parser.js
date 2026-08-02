/**
 * Разбор страниц тарифов у провайдеров без API.
 * Зависимость одна: cheerio. Селекторы лежат в sources/_html.js,
 * поэтому при редизайне правится конфиг, а не код.
 */
const CONFIGS = require('./sources/_html');

const sleep = ms => new Promise(r => setTimeout(r, ms));

// вытаскиваем первое число: "от 299 ₽/мес" -> 299, "$5.90/mo" -> 5.9, "1 062 ₽" -> 1062
function num(text) {
  if (!text) return null;
  const cleaned = String(text).replace(/ /g, ' ').replace(/(\d)\s+(\d)/g, '$1$2');
  const m = cleaned.match(/-?\d+(?:[.,]\d+)?/);
  return m ? parseFloat(m[0].replace(',', '.')) : null;
}

module.exports = async function parseHtml(slug, { timeout = 20000, delay = 1500 } = {}) {
  const cfg = CONFIGS[slug];
  if (!cfg) throw new Error('нет конфига разбора для ' + slug);
  let cheerio;
  try { cheerio = require('cheerio'); }
  catch { throw new Error('нужен пакет cheerio: npm i cheerio'); }

  const out = [];
  for (const page of cfg.pages) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeout);
    let html;
    try {
      const res = await fetch(page.url, {
        signal: ctrl.signal,
        headers: {
          'User-Agent': 'PodborVPS-PriceMonitor/1.0 (+https://podborvps.ru/methodology)',
          'Accept-Language': 'ru,en;q=0.8'
        }
      });
      if (!res.ok) throw new Error('HTTP ' + res.status + ' на ' + page.url);
      html = await res.text();
    } finally { clearTimeout(t); }

    const $ = cheerio.load(html);
    $(cfg.row).each((_, el) => {
      const row = $(el);
      const pick = sel => sel ? row.find(sel).first().text().trim() : '';
      const name = pick(cfg.fields.name);
      const price = num(pick(cfg.fields.price));
      if (!name || price == null) return;              // шапки таблиц и мусор отсеиваются
      out.push({
        id: (page.geo || 'x') + '-' + name.toLowerCase().replace(/[^a-zа-я0-9]+/gi, '-').slice(0, 40),
        name,
        cpu: num(pick(cfg.fields.cpu)),
        ram: num(pick(cfg.fields.ram)),
        disk: num(pick(cfg.fields.disk)),
        diskType: /nvme/i.test(row.text()) ? 'NVMe' : (/ssd/i.test(row.text()) ? 'SSD' : null),
        geo: page.geo,
        price,
        promoPrice: cfg.fields.promoPrice ? num(pick(cfg.fields.promoPrice)) : null,
        period: cfg.period || 'month',
        currency: cfg.currency || 'RUB',
        url: page.url
      });
    });
    await sleep(delay);   // вежливая пауза, Crawl-delay провайдеры не задают, но нагружать незачем
  }
  return out;
};
