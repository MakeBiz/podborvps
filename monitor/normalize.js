// Приведение к общему виду. Без этого цены несравнимы:
// Beget и VDSina тарифицируют посуточно, Reg.ru отдаёт час и месяц,
// Timeweb и AdminVPS помесячно со скидочной сеткой 3/6/12/24
const DAYS_IN_MONTH = 30.4375;   // средний месяц, чтобы посуточные не прыгали

function toMonthly(amount, period) {
  const a = Number(amount);
  if (!isFinite(a)) return null;
  switch (period) {
    case 'month': return a;
    case 'day':   return a * DAYS_IN_MONTH;
    case 'hour':  return a * DAYS_IN_MONTH * 24;
    case 'year':  return a / 12;
    default:      return null;
  }
}

function normalizePlan(raw, provider, rates) {
  const monthly = toMonthly(raw.price, raw.period || 'month');
  if (monthly == null) return null;
  const cur = (raw.currency || 'RUB').toUpperCase();
  const rate = cur === 'RUB' ? 1 : (rates[cur] || null);
  return {
    id: provider + ':' + raw.id,
    providerSlug: provider,
    name: String(raw.name || '').trim(),
    cpu: raw.cpu ?? null,
    ram: raw.ram ?? null,               // ГБ
    disk: raw.disk ?? null,             // ГБ
    diskType: raw.diskType || null,
    geo: raw.geo || null,
    price: Math.round(monthly * 100) / 100,
    currency: cur,
    priceRub: rate ? Math.round(monthly * rate) : null,
    // промо и базовая цена хранятся раздельно, иначе история отравляется акциями
    promoPrice: raw.promoPrice != null ? Math.round(toMonthly(raw.promoPrice, raw.period || 'month') * 100) / 100 : null,
    renewalPrice: raw.renewalPrice != null ? Math.round(toMonthly(raw.renewalPrice, raw.period || 'month') * 100) / 100 : null,
    billingPeriod: raw.period || 'month',
    url: raw.url || null,
    source: raw.source,                 // api | html | manual
    verifiedAt: raw.verifiedAt
  };
}

module.exports = { toMonthly, normalizePlan, DAYS_IN_MONTH };
