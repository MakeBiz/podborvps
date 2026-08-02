// Разбор HTML для провайдеров без API. Селекторы вынесены в конфиг:
// когда провайдер переверстает страницу, правится одна строка, а не код
module.exports = {
  adminvps: {
    slug: 'adminvps',
    currency: 'RUB',
    pages: [
      { url: 'https://adminvps.ru/vps/vps_russia.php',    geo: 'ru' },
      { url: 'https://adminvps.ru/vps/vps_germany.php',   geo: 'de' },
      { url: 'https://adminvps.ru/vps/vps_holland.php',   geo: 'nl' },
      { url: 'https://adminvps.ru/vps/vps_kazakhstan.php',geo: 'kz' },
      { url: 'https://adminvps.ru/vps/vps_finland.php',   geo: 'fi' },
      { url: 'https://adminvps.ru/vps/vps_poland.php',    geo: 'pl' }
    ],
    row: 'table tr, .tariff-row',
    fields: { name:'td:nth-child(1)', cpu:'td:nth-child(2)', ram:'td:nth-child(3)', disk:'td:nth-child(4)', price:'td:last-child' },
    period: 'month'
  },
  beget: {
    slug: 'beget', currency: 'RUB',
    pages: [{ url: 'https://beget.com/ru/vps', geo: 'ru' }],
    row: '[class*=tariff], [class*=plan]',
    fields: { name:'[class*=name]', cpu:'[class*=cpu]', ram:'[class*=ram]', disk:'[class*=disk]', price:'[class*=price]' },
    period: 'day'    // Beget тарифицирует посуточно, нормализация приведёт к месяцу
  },
  truehost: {
    slug: 'truehost', currency: 'USD',
    pages: [{ url: 'https://truehost.com/vps-hosting/', geo: 'global' }],
    row: '.pricing-item, .package',
    fields: { name:'.package-name', cpu:'.cpu', ram:'.ram', disk:'.disk', price:'.price' },
    period: 'month'
  },
  ultahost: {
    slug: 'ultahost', currency: 'USD',
    pages: [{ url: 'https://ultahost.com/vps-hosting', geo: 'global' }],
    row: '.plan-card',
    // на странице акционная и базовая цена рядом, берём обе, иначе история отравится акцией
    fields: { name:'.plan-title', cpu:'.cpu', ram:'.ram', disk:'.disk', price:'.price-old', promoPrice:'.price-new' },
    period: 'month'
  },
  aeserver: {
    slug: 'aeserver', currency: 'AED',
    pages: [{ url: 'https://www.aeserver.com/vps-hosting', geo: 'uae' }],
    row: 'table tr',
    fields: { name:'td:nth-child(1)', cpu:'td:nth-child(2)', ram:'td:nth-child(3)', disk:'td:nth-child(4)', price:'td:last-child' },
    period: 'month'
  },
  firstvds: {
    slug: 'firstvds', currency: 'RUB',
    pages: [{ url: 'https://firstvds.ru/products/vds-vps', geo: 'ru' }],
    row: '[class*=tariff]',
    fields: { name:'[class*=title]', cpu:'[class*=cpu]', ram:'[class*=ram]', disk:'[class*=disk]', price:'[class*=price]' },
    period: 'month'
  },
  ishosting: {
    slug: 'ishosting', currency: 'USD',
    pages: [{ url: 'https://ishosting.com/en/vps', geo: 'global' }],
    row: '[class*=tariff], [class*=card]',
    fields: { name:'[class*=name]', cpu:'[class*=cpu]', ram:'[class*=ram]', disk:'[class*=disk]', price:'[class*=price]' },
    period: 'month'
  }
};
