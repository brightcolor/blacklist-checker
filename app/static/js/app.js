const api = '/api/v1';
let token = localStorage.getItem('rb_token') || null;

const authCard = document.getElementById('auth-card');
const appGrid = document.getElementById('app-grid');
const kpisEl = document.getElementById('kpis');
const monitorListEl = document.getElementById('monitor-list');
const listTableEl = document.getElementById('list-table');
const checkResultEl = document.getElementById('check-result');

async function call(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${api}${path}`, { ...options, headers });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }
  return res.json();
}

function setTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem('rb_theme', theme);
}

document.getElementById('theme-toggle').addEventListener('click', () => {
  setTheme(document.body.dataset.theme === 'dark' ? 'light' : 'dark');
});

document.getElementById('logout').addEventListener('click', () => {
  token = null;
  localStorage.removeItem('rb_token');
  renderAuthState();
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = { email: fd.get('email'), password: fd.get('password') };
  try {
    const data = await call('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
    token = data.access_token;
    localStorage.setItem('rb_token', token);
    renderAuthState();
    await refreshAll();
  } catch (err) {
    alert(`Login fehlgeschlagen: ${err.message}`);
  }
});

document.getElementById('check-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = { target_type: fd.get('target_type'), target_value: fd.get('target_value') };
  try {
    const run = await call('/checks/run', { method: 'POST', body: JSON.stringify(payload) });
    renderCheck(run);
  } catch (err) {
    checkResultEl.innerHTML = `<p class="status-error">Fehler: ${err.message}</p>`;
  }
});

document.getElementById('refresh-monitors').addEventListener('click', refreshMonitors);
document.getElementById('refresh-lists').addEventListener('click', refreshLists);

function renderAuthState() {
  if (!token) {
    authCard.classList.remove('hidden');
    appGrid.classList.add('hidden');
    return;
  }
  authCard.classList.add('hidden');
  appGrid.classList.remove('hidden');
}

function renderKpis(data) {
  const mapping = [
    ['Monitore', data.monitors_total],
    ['Aktuell gelistet', data.currently_listed],
    ['Neue Listings (24h)', data.new_listings_today],
    ['Fehlchecks (24h)', data.failed_checks_last_24h],
    ['Alerts (24h)', data.alerts_last_24h],
  ];
  kpisEl.innerHTML = mapping
    .map(([label, value]) => `<div class="kpi"><small>${label}</small><strong>${value}</strong></div>`)
    .join('');
}

function renderMonitors(items) {
  if (!items.length) {
    monitorListEl.innerHTML = '<small>Keine Monitore vorhanden.</small>';
    return;
  }
  const rows = items.map((m) => `<tr>
    <td>${m.name}</td>
    <td>${m.target_type}:${m.target_value}</td>
    <td><span class="status-${m.last_status}">${m.last_status}</span></td>
    <td>${m.interval_minutes}m</td>
    <td>${m.last_run_at || '-'}</td>
    <td>${m.next_run_at || '-'}</td>
  </tr>`).join('');
  monitorListEl.innerHTML = `<table class="table"><thead><tr><th>Name</th><th>Ziel</th><th>Status</th><th>Intervall</th><th>Letzter Check</th><th>Nächster Check</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderLists(items) {
  const rows = items.map((l) => `<tr>
    <td>${l.name}</td>
    <td>${l.list_type}</td>
    <td>${l.dns_zone}</td>
    <td>${l.health_score}</td>
    <td>${l.is_degraded ? '<span class="status-error">degradiert</span>' : '<span class="status-ok">ok</span>'}</td>
  </tr>`).join('');
  listTableEl.innerHTML = `<table class="table"><thead><tr><th>Liste</th><th>Typ</th><th>Zone</th><th>Health</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderCheck(run) {
  const rows = run.results.map((r) => `<tr>
      <td>${r.list_name}</td>
      <td>${r.status}</td>
      <td>${r.answer_code || '-'}</td>
      <td>${r.txt_record || '-'}</td>
      <td>${r.raw_error || '-'}</td>
    </tr>`).join('');
  const fcrdnsLine = run.fcrdns ? `<p>FCrDNS: ${run.fcrdns.ok ? 'ok' : 'failed'} (${run.fcrdns.ptr || run.fcrdns.reason || '-'})</p>` : '';
  checkResultEl.innerHTML = `
    <p>Overall: <span class="status-${run.overall_status}">${run.overall_status}</span> | gelistet=${run.listed_count} | fehler=${run.error_count}</p>
    ${fcrdnsLine}
    <table class="table"><thead><tr><th>Liste</th><th>Status</th><th>Code</th><th>TXT</th><th>Fehler</th></tr></thead><tbody>${rows}</tbody></table>
  `;
}

async function refreshDashboard() {
  const data = await call('/dashboard');
  renderKpis(data);
}

async function refreshMonitors() {
  const data = await call('/monitors');
  renderMonitors(data);
}

async function refreshLists() {
  const data = await call('/lists');
  renderLists(data);
}

async function refreshAll() {
  await Promise.all([refreshDashboard(), refreshMonitors(), refreshLists()]);
}

(function init() {
  const savedTheme = localStorage.getItem('rb_theme') || 'dark';
  setTheme(savedTheme);
  renderAuthState();
  if (token) {
    refreshAll().catch(() => {
      token = null;
      localStorage.removeItem('rb_token');
      renderAuthState();
    });
  }
})();
