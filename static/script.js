const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const fmt = (value) => {
  const num = Number(value || 0);
  return Number.isInteger(num)
    ? num.toLocaleString('ru-RU')
    : num.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
};

const byId = (id) => document.getElementById(id);
let currentData = null;

function renderRows(items) {
  const body = byId('historyBody');
  body.innerHTML = '';
  if (!items || !items.length) {
    body.innerHTML = '<div class="empty">Нет данных</div>';
    return;
  }
  items.forEach((item) => {
    const row = document.createElement('div');
    row.className = 'history-row';
    row.innerHTML = `
      <div class="row-amount">${fmt(item.amount)}</div>
      <div class="row-time">${item.at || ''}</div>
    `;
    body.appendChild(row);
  });
}

function render(data) {
  currentData = data;
  byId('balanceValue').textContent = fmt(data.balance);
  byId('spreadValue').textContent = fmt(data.spread);
  byId('payoutsValue').textContent = fmt(data.payouts);
  byId('incomeValue').textContent = fmt(data.income);
  byId('fixedValue').textContent = fmt(data.fixed);
  byId('chatTitle').textContent = data.chat_title || 'Группа';
  byId('historyTitle').textContent = 'Последние выдачи';
  renderRows(data.history?.payouts || []);
}

async function load() {
  const startParam = tg?.initDataUnsafe?.start_param || new URLSearchParams(location.search).get('startapp') || '';
  const match = String(startParam).match(/group_(-?\d+)/);
  if (!match) {
    byId('historyBody').innerHTML = '<div class="empty">Нет chat_id в startapp</div>';
    return;
  }
  const chatId = match[1];
  const res = await fetch(`/api/chat/${encodeURIComponent(chatId)}`);
  if (!res.ok) {
    byId('historyBody').innerHTML = '<div class="empty">Не удалось загрузить данные</div>';
    return;
  }
  const data = await res.json();
  render(data);
}

byId('refreshBtn').addEventListener('click', load);
document.querySelectorAll('[data-open]').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (!currentData) return;
    const key = btn.dataset.open;
    const titleMap = {
      balance: 'Движения по балансу',
      spread: 'Спред за день',
      payouts: 'История выдач',
      income: 'История приходов',
      fixed: 'История фиксов',
    };
    byId('historyTitle').textContent = titleMap[key] || 'История';
    if (key === 'balance') {
      renderRows([
        { amount: currentData.balance, at: 'Текущий баланс' },
        { amount: currentData.opening_balance, at: 'Старт дня' },
      ]);
      return;
    }
    if (key === 'spread') {
      renderRows([{ amount: currentData.spread, at: 'Текущий спред' }]);
      return;
    }
    renderRows(currentData.history?.[key] || []);
  });
});

load();
setInterval(load, 5000);
