// Реестр источников. tier определяет частоту и доверие к данным.
// tier 1 = официальный API, забираем ежедневно, точность высокая
// tier 2 = разбор HTML, забираем через день, ломается при редизайне
// tier 3 = цены за JS-калькулятором, только ручная сверка раз в квартал
module.exports = [
  { slug:'vdsina',    tier:1, kind:'api',  auth:'VDSINA_TOKEN',
    note:'цена числом плюс период тарификации и отдельная цена бэкапа' },
  { slug:'timeweb',   tier:1, kind:'api',  auth:'TIMEWEB_TOKEN',
    note:'токен можно сделать бессрочным, есть конфигуратор с ценой за ядро и ГБ' },
  { slug:'regru',     tier:1, kind:'api',  auth:'REGRU_CLOUDVPS_TOKEN',
    note:'маркетинговые страницы без JS пустые, только API' },
  { slug:'ruvds',     tier:1, kind:'api',  auth:'RUVDS_TOKEN',
    note:'двухшаговая авторизация, sessionToken можно бессрочный' },
  { slug:'hostman',   tier:1, kind:'api',  auth:'HOSTMAN_TOKEN',
    note:'база hostman.com/api/v1, НЕ api.hostman.com' },
  { slug:'datapacket',tier:1, kind:'api',  auth:'DATAPACKET_TOKEN',
    note:'GraphQL, ключ можно сделать read-only' },
  { slug:'adminvps',  tier:2, kind:'html', auth:null,
    note:'10 страниц по локациям, обычный серверный HTML' },
  { slug:'beget',     tier:2, kind:'html', auth:null,
    note:'тарификация посуточная, приводить к месяцу' },
  { slug:'truehost',  tier:2, kind:'html', auth:null, note:'robots полностью открыт' },
  { slug:'ultahost',  tier:2, kind:'html', auth:null,
    note:'ВАЖНО: на странице акционная и базовая цена рядом, забирать обе' },
  { slug:'aeserver',  tier:2, kind:'html', auth:null, note:'Cloudflare на сайте, GET проходит' },
  { slug:'firstvds',  tier:2, kind:'html', auth:null, note:'API требует аккаунт и белый список IP' },
  { slug:'ishosting', tier:2, kind:'html', auth:null,
    note:'в API нет прайса, цена только через order/validate, поэтому HTML' },
  { slug:'selectel',  tier:3, kind:'manual', auth:null,
    note:'детальные цены за JS-калькулятором, prices.selectel.ru закрыт robots' },
  { slug:'vpsorg',    tier:3, kind:'manual', auth:null, note:'на странице только цены от' }
];
