// Hostman. Внимание на базовый URL: работает hostman.com/api/v1, а не api.hostman.com/v1
const BASE = 'https://hostman.com/api/v1';

module.exports = {
  slug: 'hostman',
  async fetchPlans({ fetchJson, env }) {
    const token = env.HOSTMAN_TOKEN;
    if (!token) throw new Error('нет HOSTMAN_TOKEN');
    const data = await fetchJson(BASE + '/presets/servers', {
      headers: { Authorization: 'Bearer ' + token }
    });
    const list = data.server_presets || data.presets || [];
    return list.map(p => ({
      id: String(p.id),
      name: p.description_short || p.description || ('preset ' + p.id),
      cpu: p.cpu,
      ram: p.ram ? Math.round(p.ram / 1024) : null,
      disk: p.disk ? Math.round(p.disk / 1024) : null,
      diskType: p.disk_type || null,
      geo: p.location || null,
      price: p.price,
      period: 'month',
      currency: 'USD',
      url: 'https://hostman.com/pricing/'
    }));
  }
};
