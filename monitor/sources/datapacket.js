// DataPacket, GraphQL. Ключ можно завести read-only
const ENDPOINT = 'https://api.datapacket.com/v0/graphql';
const QUERY = `query { provisioningConfigurations {
  id name cpuCores memoryGb location { name region }
  monthlyHwPrice { amount currency }
} }`;

module.exports = {
  slug: 'datapacket',
  async fetchPlans({ fetchJson, env }) {
    const token = env.DATAPACKET_TOKEN;
    if (!token) throw new Error('нет DATAPACKET_TOKEN');
    const data = await fetchJson(ENDPOINT, {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: QUERY })
    });
    const list = (data.data && data.data.provisioningConfigurations) || [];
    return list.map(c => ({
      id: String(c.id),
      name: c.name,
      cpu: c.cpuCores, ram: c.memoryGb, disk: null, diskType: null,
      geo: c.location && c.location.region,
      price: c.monthlyHwPrice && c.monthlyHwPrice.amount,
      period: 'month',
      currency: (c.monthlyHwPrice && c.monthlyHwPrice.currency) || 'USD',
      url: 'https://www.datapacket.com/pricing'
    }));
  }
};
