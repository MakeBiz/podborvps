// RUVDS. Двухшаговая авторизация, endless=1 даёт бессрочный sessionToken
const BASE = 'https://ruvds.com/api';

module.exports = {
  slug: 'ruvds',
  async fetchPlans({ fetchJson, env }) {
    const { RUVDS_KEY, RUVDS_USER, RUVDS_PASS } = env;
    if (!RUVDS_KEY) throw new Error('нет RUVDS_KEY');
    const auth = await fetchJson(
      `${BASE}/logon/?key=${encodeURIComponent(RUVDS_KEY)}&username=${encodeURIComponent(RUVDS_USER)}&password=${encodeURIComponent(RUVDS_PASS)}&endless=1`
    );
    const t = auth.sessionToken || auth.session_token;
    const data = await fetchJson(BASE + '/tariff/', { headers: { Authorization: t } });
    const list = data.tariffs || data.data || [];
    // RUVDS отдаёт цену за единицу ресурса, а не готовые тарифы: собираем типовые конфигурации
    return list.map(t2 => ({
      id: String(t2.id ?? t2.tariffId ?? 'tariff'),
      name: t2.name || 'Тариф',
      cpu: t2.cpu ?? null, ram: t2.ram ?? null, disk: t2.disk ?? null,
      diskType: 'NVMe', geo: t2.datacenter || null,
      price: t2.price ?? t2.cost ?? null,
      period: 'month', currency: 'RUB',
      url: 'https://ruvds.com/ru-rub/'
    }));
  }
};
