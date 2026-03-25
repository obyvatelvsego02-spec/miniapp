const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor('#0b1730');
    tg.setBackgroundColor('#07111f');
  } catch (_) {}
}

const byId = (id) => document.getElementById(id);

const fmt = (value) => {
  const num = Number(value || 0);
  return num.toLocaleString('ru-RU', {
    minimumFractionDigits: Number.isInteger(num) ? 0 : 2,
    maximumFractionDigits: 2,
  });
};

let currentData = null;
let currentTab = 'payouts';

function setMetric(id, value, suffix = '') {
  byId(id).textContent = `${fmt(value)}${suffix}`;
}

function setTabs(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach((btn) => {
    btn.classList.toggle('is-active', btn.dataset.open === tab);
  });
}

function emptyState(text = 'Нет данных') {
  return `
    <div class="empty-state">
      <div class="empty-state__icon">∿</div>
      <div class="empty-state__title">${text}</div>
      <div class="empty-state__text">Как только в чате появятся операции, они будут видны здесь.</div>
    </div>
  `;
}

function rowTemplate(id, title, subtitle, amount, kind = 'neutral') {
  const cls = kind === 'negative' ? 'is-negative' : kind === 'positive' ? 'is-positive' : '';
  const clickable = id ? 'is-clickable' : '';

  return `
    <div class="history-row ${clickable}" ${id ? `data-operation-id="${id}"` : ''}>
      <div class="history-row__dot"></div>
      <div class="history-row__main">
        <div class="history-row__title">${title}</div>
        <div class="history-row__subtitle">${subtitle}</div>
      </div>
      <div class="history-row__amount ${cls}">${fmt(amount)}</div>
    </div>
  `;
}

function renderList(tab, data) {
  const body = byId('historyBody');
  const title = byId('historyTitle');
  const badge = byId('historyBadge');
  const history = data.history || {};

  const config = {
    payouts: { title: 'Последние выдачи', badge: 'Сегодня' },
    income: { title: 'История приходов', badge: `${fmt(data.income)} за день` },
    fixed: { title: 'История фиксов', badge: `${fmt(data.fixed)} за день` },
    balance: { title: 'Движение баланса', badge: 'Текущая точка' },
    spread: { title: 'Спред за день', badge: 'Текущий итог' },
  };

  title.textContent = config[tab].title;
  badge.textContent = config[tab].badge;

  if (tab === 'balance') {
    body.innerHTML = [
      rowTemplate(null, 'Текущий баланс', 'После всех операций', data.balance, data.balance < 0 ? 'negative' : 'positive'),
      rowTemplate(null, 'Старт дня', 'Остаток на начало дня', data.opening_balance),
      rowTemplate(null, 'Выдачи', 'Списано за день', -Math.abs(data.payouts), 'negative'),
    ].join('');
    return;
  }

  if (tab === 'spread') {
    body.innerHTML = rowTemplate(
      null,
      'Текущий спред',
      'Приходы минус фиксы',
      data.spread,
      data.spread < 0 ? 'negative' : 'positive'
    );
    return;
  }

  const items = history[tab] || [];
  if (!items.length) {
    body.innerHTML = emptyState('Пока пусто');
    return;
  }

  body.innerHTML = items.map((item, index) => {
    const amount = Number(item.amount || 0);

    const labels = {
      payouts: 'Выдача',
      income: 'Приход',
      fixed: 'Фикс',
    };

    const kinds = {
      payouts: 'negative',
      income: 'positive',
      fixed: 'neutral',
    };

    return rowTemplate(
      item.id,
      `${labels[tab]} #${items.length - index}`,
      item.at || 'Без времени',
      amount,
      kinds[tab]
    );
  }).join('');
}

function render(data, chatId) {
  currentData = data;

  setMetric('balanceValue', data.balance);
  setMetric('spreadValue', data.spread);
  setMetric('manualSpreadValue', data.manual_spread);
  setMetric('payoutsValue', data.payouts);
  setMetric('incomeValue', data.income);
  setMetric('fixedValue', data.fixed);

  byId('chatTitle').textContent = `${data.chat_title || 'Группа'} · chat_id: ${chatId}`;

  renderList(currentTab, data);
}

function resolveChatId() {
  const urlParams = new URLSearchParams(location.search);
  const directChatId = urlParams.get('chat_id');
  const startParam = tg?.initDataUnsafe?.start_param || urlParams.get('startapp') || '';
  const match = String(startParam).match(/group_(-?\d+)/);

  return directChatId || (match ? match[1] : null);
}

async function deleteOperation(operationId, chatId) {
  const ok = window.confirm('Удалить эту операцию?');
  if (!ok) return;

  const apiUrl = `https://miniapp-production-2f44.up.railway.app/api/operation/delete/${operationId}?chat_id=${chatId}`;

  try {
    const res = await fetch(apiUrl, { method: 'POST' });
    const data = await res.json();

    if (!data.ok) {
      throw new Error(data.error || 'delete failed');
    }

    render({
      ...currentData,
      ...data
    }, chatId);

  } catch (e) {
    console.error(e);
    alert('Ошибка удаления');
  }
}

async function load() {
  const chatId = resolveChatId();

  if (!chatId) {
    byId('historyBody').innerHTML = emptyState('Нет chat_id');
    return;
  }

  const res = await fetch(
    `https://miniapp-production-2f44.up.railway.app/api/dashboard/${chatId}?t=${Date.now()}`
  );

  const data = await res.json();
  render(data, chatId);
}

byId('historyBody').addEventListener('click', (e) => {
  const row = e.target.closest('[data-operation-id]');
  if (!row) return;

  const id = row.dataset.operationId;
  const chatId = resolveChatId();

  if (!id || !chatId) return;

  deleteOperation(id, chatId);
});

byId('refreshBtn').addEventListener('click', load);

document.querySelectorAll('[data-open]').forEach((btn) => {
  btn.addEventListener('click', () => {
    setTabs(btn.dataset.open);
    if (currentData) renderList(currentTab, currentData);
  });
});

load();
setInterval(load, 5000);
