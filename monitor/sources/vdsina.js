// VDSina. Токен: POST /v1/auth с email и паролем обычного аккаунта
const BASE = 'https://userapi.vdsina.ru/v1';

module.exports = {
  slug: 'vdsina',
  async fetchPlans({ fetchJson, env }) {
    const token = env.VDSINA_TOKEN;
    if (!token) throw new Error('нет VDSINA_TOKEN');
    const h = { Authorization: token };
    const groups = (await fetchJson(BASE + '/server-group', { headers: h })).data || [];
    const out = [];
    for (const g of groups) {
      const plans = (await fetchJson(BASE + '/server-plan/' + g.id, { headers: h })).data || [];
      for (const p of plans) {
        const d = p.data || {};
        out.push({
          id: String(p.id),
          name: p.name,
          cpu: d.cpu && d.cpu.value,
          ram: d.ram && d.ram.value,
          disk: d.disk && d.disk.value,
          diskType: 'NVMe',
          geo: null,
          price: p.cost,
          period: p.period === 'day' ? 'day' : 'month',   // у VDSina посуточно
          currency: 'RUB',
          url: 'https://vdsina.ru/'
        });
      }
    }
    return out;
  }
};
