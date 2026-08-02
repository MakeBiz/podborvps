// Сравнение вчерашнего и сегодняшнего снимка.
// Результат идёт в журнал изменений и в раздел новостей на сайте
function key(p) { return p.id; }

function comparePlans(prev, next) {
  const a = new Map(prev.map(p => [key(p), p]));
  const b = new Map(next.map(p => [key(p), p]));
  const changes = { priceUp: [], priceDown: [], added: [], removed: [], specChanged: [] };

  for (const [k, np] of b) {
    const op = a.get(k);
    if (!op) { changes.added.push(np); continue; }
    if (op.price !== np.price) {
      const rec = { plan: np, from: op.price, to: np.price,
                    pct: op.price ? Math.round((np.price - op.price) / op.price * 1000) / 10 : null };
      (np.price > op.price ? changes.priceUp : changes.priceDown).push(rec);
    }
    for (const f of ['cpu', 'ram', 'disk', 'diskType']) {
      if (op[f] !== np[f]) { changes.specChanged.push({ plan: np, field: f, from: op[f], to: np[f] }); break; }
    }
  }
  for (const [k, op] of a) if (!b.has(k)) changes.removed.push(op);
  return changes;
}

// Санитарная проверка: защищает от публикации мусора, если вёрстка поехала
function sanityCheck(providerSlug, prev, next) {
  const problems = [];
  if (!next.length) problems.push('источник вернул ноль тарифов');
  if (prev.length && next.length < prev.length * 0.5)
    problems.push(`тарифов стало вдвое меньше: было ${prev.length}, стало ${next.length}`);
  const weird = next.filter(p => !(p.price > 0) || p.price > 5e6);
  if (weird.length) problems.push(`подозрительные цены у ${weird.length} тарифов`);
  const noName = next.filter(p => !p.name);
  if (noName.length > next.length * 0.3) problems.push('у трети тарифов не разобралось название');
  // резкий скачок средней цены обычно означает, что парсер поймал не ту колонку
  if (prev.length && next.length) {
    const avg = l => l.reduce((s, p) => s + (p.price || 0), 0) / l.length;
    const ap = avg(prev), an = avg(next);
    if (ap && (an > ap * 3 || an < ap / 3))
      problems.push(`средняя цена изменилась в разы: ${Math.round(ap)} -> ${Math.round(an)}`);
  }
  return problems;
}

module.exports = { comparePlans, sanityCheck };
