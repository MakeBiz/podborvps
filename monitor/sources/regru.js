// Reg.ru CloudVPS. Маркетинговые страницы /vps/ без JS пустые, поэтому только API
const BASE = 'https://api.cloudvps.reg.ru/v2';
const REGIONS = ['openstack-msk1', 'openstack-spb1'];

module.exports = {
  slug: 'regru',
  async fetchPlans({ fetchJson, env }) {
    const token = env.REGRU_CLOUDVPS_TOKEN;
    if (!token) throw new Error('нет REGRU_CLOUDVPS_TOKEN');
    const out = [];
    for (const region of REGIONS) {
      const data = await fetchJson(`${BASE}/plans?region=${region}&items_per_page=100`, {
        headers: { Authorization: 'Bearer ' + token }
      });
      for (const p of (data.plans || [])) {
        out.push({
          id: p.slug || String(p.id),
          name: p.name,
          cpu: p.vcpus,
          ram: p.memory ? Math.round(p.memory / 1024) : null,   // приходит в МБ
          disk: p.disk,
          diskType: 'NVMe',
          geo: region.includes('msk') ? 'ru-msk' : 'ru-spb',
          price: p.price_per_month,
          period: 'month',
          currency: 'RUB',
          url: 'https://www.reg.ru/vps/cloud'
        });
      }
    }
    return out;
  }
};
