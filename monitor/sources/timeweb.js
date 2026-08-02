// Timeweb Cloud. Токен: панель, Настройки, "API и Terraform", можно бессрочный
const BASE = 'https://api.timeweb.cloud/api/v1';

module.exports = {
  slug: 'timeweb',
  async fetchPlans({ fetchJson, env }) {
    const token = env.TIMEWEB_TOKEN;
    if (!token) throw new Error('нет TIMEWEB_TOKEN');
    const data = await fetchJson(BASE + '/presets/servers', {
      headers: { Authorization: 'Bearer ' + token }
    });
    const list = data.server_presets || data.presets || [];
    return list.map(p => ({
      id: String(p.id),
      name: p.description_short || p.description || ('preset ' + p.id),
      cpu: p.cpu,
      ram: p.ram ? Math.round(p.ram / 1024) : null,      // приходит в МБ
      disk: p.disk ? Math.round(p.disk / 1024) : null,   // приходит в МБ
      diskType: p.disk_type || null,
      geo: p.location || null,
      price: p.price,
      period: 'month',
      currency: 'RUB',
      url: 'https://timeweb.cloud/services/vds-vps'
    }));
  }
};
