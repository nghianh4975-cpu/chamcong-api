/* ============================================
   API Helper
   ============================================ */
// API_BASE: tự động phát hiện environment
// - Local dev: /api
// - Render: /api (cùng domain với frontend)
// - Muốn đổi domain khác: sửa RENDER_API_URL bên dưới
const RENDER_API_URL = ''; // VD: 'https://chamcong.onrender.com' — để trống = dùng relative path
const API_BASE = RENDER_API_URL ? `${RENDER_API_URL}/api` : '/api';

const api = {
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  username: localStorage.getItem('username'),

  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers: { ...headers, ...options.headers } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401) { this.logout(); window.location.reload(); }
      // FastAPI 422 trả detail là array, 200/400 trả detail là string
      let msg = data.detail;
      if (Array.isArray(msg)) {
        msg = msg.map(e => e.loc ? `${e.loc.join('.')}: ${e.msg}` : e.msg || JSON.stringify(e)).join(' | ');
      } else if (typeof msg !== 'string') {
        msg = JSON.stringify(msg) || 'Lỗi không xác định';
      }
      throw new Error(msg || 'Lỗi không xác định');
    }
    return data;
  },

  get(path) { return this.request(path); },
  post(path, body) { return this.request(path, { method: 'POST', body: JSON.stringify(body) }); },
  put(path, body) { return this.request(path, { method: 'PUT', body: JSON.stringify(body) }); },
  del(path) { return this.request(path, { method: 'DELETE' }); },

  setAuth(token, role, username) {
    this.token = token; this.role = role; this.username = username;
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    localStorage.setItem('username', username);
  },

  logout() {
    this.token = null; this.role = null; this.username = null;
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
  }
};

/* ============================================
   Toast Notifications
   ============================================ */
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'alert-circle'}"></i><span>${message}</span>`;
  container.appendChild(toast);
  lucide.createIcons();
  setTimeout(() => toast.remove(), 4000);
}

/* ============================================
   Utilities
   ============================================ */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatTime(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(num) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(num);
}

function getStatusBadge(status) {
  const map = {
    ON_TIME: { cls: 'badge-success', text: 'Đúng giờ' },
    LATE: { cls: 'badge-warning', text: 'Đi muộn' },
    EARLY_LEAVE: { cls: 'badge-warning', text: 'Về sớm' },
    ABSENT: { cls: 'badge-danger', text: 'Vắng' },
    COMPLETE: { cls: 'badge-info', text: 'Hoàn thành' },
    draft: { cls: 'badge-gray', text: 'Nháp' },
    confirmed: { cls: 'badge-warning', text: 'Đã duyệt' },
    paid: { cls: 'badge-success', text: 'Đã thanh toán' },
  };
  const s = map[status] || { cls: 'badge-gray', text: status };
  return `<span class="badge ${s.cls}">${s.text}</span>`;
}

function getToday() {
  const now = new Date();
  return now.toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' });
}

/* ============================================
   Router
   ============================================ */
let currentRoute = '';
const routes = {
  '/': 'login',
  '/login': 'login',
  '/admin': 'admin',
  '/admin/employees': 'admin-employees',
  '/admin/attendance': 'admin-attendance',
  '/admin/salary': 'admin-salary',
  '/attendance': 'attendance',
  '/attendance/history': 'attendance-history',
  '/pos': 'pos',
};

function navigate(path) {
  window.location.hash = path;
}

function getRoute() {
  const hash = window.location.hash.slice(1) || '/';
  if (api.token) {
    if (hash === '/' || hash === '/login') navigate(api.role === 'employee' ? '/attendance' : '/admin');
    return hash;
  } else {
    if (!['/', '/login'].includes(hash)) navigate('/login');
    return hash === '/' ? '/login' : hash;
  }
}

window.addEventListener('hashchange', render);

/* ============================================
   Modal Helper
   ============================================ */
function openModal(title, bodyHtml, footerHtml = '') {
  let overlay = document.getElementById('modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'modal-overlay';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `<div class="modal"><div class="modal-header"><h3 class="modal-title"></h3><button class="modal-close" onclick="closeModal()">&times;</button></div><div class="modal-body"></div><div class="modal-footer"></div></div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  }
  overlay.querySelector('.modal-title').textContent = title;
  overlay.querySelector('.modal-body').innerHTML = bodyHtml;
  overlay.querySelector('.modal-footer').innerHTML = footerHtml;
  overlay.classList.add('active');
  lucide.createIcons();
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

/* ============================================
   Page: Login
   ============================================ */
function renderLogin() {
  return `
    <div class="login-page">
      <div class="login-card">
        <div class="login-logo">
          <div class="login-logo-icon">CC</div>
          <div class="login-title">Chấm Công Thông Minh</div>
          <div class="login-subtitle">Đăng nhập để tiếp tục</div>
        </div>
        <div class="login-error" id="login-error"></div>
        <form id="login-form" onsubmit="handleLogin(event)">
          <div class="form-group">
            <label class="form-label">Tên đăng nhập</label>
            <input type="text" class="form-input" id="login-username" placeholder="Nhập tên đăng nhập" required autocomplete="username">
          </div>
          <div class="form-group">
            <label class="form-label">Mật khẩu</label>
            <input type="password" class="form-input" id="login-password" placeholder="Nhập mật khẩu" required autocomplete="current-password">
          </div>
          <button type="submit" class="btn btn-primary btn-block btn-lg" id="login-btn">Đăng nhập</button>
        </form>
      </div>
    </div>
  `;
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('login-btn');
  const errEl = document.getElementById('login-error');
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Đang đăng nhập...';
  errEl.style.display = 'none';

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.detail || 'Đăng nhập thất bại'); }

    api.setAuth(data.access_token, data.role || 'admin', username);
    showToast('Đăng nhập thành công!');
    navigate(data.role === 'employee' ? '/attendance' : '/admin');
    render();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Đăng nhập';
  }
}

/* ============================================
   Page: Attendance (Employee)
   ============================================ */
async function renderAttendance() {
  const emp = await getEmployeeInfo();
  const myCode = emp ? emp.employee_code : '';
  const showManual = !myCode;
  return `
    <div class="attendance-page">
      <div class="attendance-header">
        <h2>Xin chào, ${emp ? emp.full_name : api.username}!</h2>
        <p>Chấm công hôm nay</p>
      </div>
      <div class="attendance-content">
        <div class="attendance-card">
          <div class="attendance-time" id="current-time">--:--:--</div>
          <div class="attendance-date" id="current-date">${getToday()}</div>
          <hr class="attendance-divider">
          <div class="attendance-tabs">
            <button class="attendance-tab active" onclick="switchAttTab('qrscan', this)">Quét QR</button>
            ${showManual ? '<button class="attendance-tab" onclick="switchAttTab(\'manual\', this)">Nhập mã</button>' : ''}
            <button class="attendance-tab" onclick="switchAttTab('checkout', this)">Chấm ra</button>
            <button class="attendance-tab" onclick="switchAttTab('passtime', this)">Pass Time</button>
          </div>
          <div id="att-qrscan-tab">
            <div id="qrscan-wrapper">
              <div id="qr-reader"></div>
              <div id="qrscan-result" class="attendance-result" style="margin-top:12px;"></div>
            </div>
          </div>
          ${showManual ? `
          <div id="att-manual-tab" class="hidden">
            <div class="attendance-input-group">
              <label class="form-label">Mã nhân viên</label>
              <input type="text" class="form-input" id="att-emp-code" placeholder="VD: NV001" autocomplete="off">
            </div>
            <div class="attendance-input-group">
              <label class="form-label">Mã PIN</label>
              <input type="password" class="form-input" id="att-pin" placeholder="Nhập mã PIN" autocomplete="off">
            </div>
            <button class="btn btn-primary btn-block btn-lg attendance-btn" onclick="handleCheckIn()">
              <i data-lucide="log-in"></i> Chấm công vào
            </button>
          </div>
          ` : ''}
          <div id="att-checkout-tab" class="hidden">
            <div class="attendance-input-group">
              <label class="form-label">Mã nhân viên</label>
              <input type="text" class="form-input" id="att-emp-code-out" placeholder="${myCode || 'Nhập mã NV'}" value="${myCode}" ${myCode ? 'readonly' : ''} autocomplete="off">
            </div>
            <button class="btn btn-danger btn-block btn-lg attendance-btn" onclick="handleCheckOut()">
              <i data-lucide="log-out"></i> Chấm công ra
            </button>
          </div>
          <div id="att-passtime-tab" class="hidden">
            <div id="passtime-form">
              <div class="attendance-input-group">
                <label class="form-label">Số tiền Pass Time (VNĐ)</label>
                <input type="number" class="form-input" id="pt-amount" placeholder="VD: 50000" min="1000" step="1000">
              </div>
              <div class="attendance-input-group">
                <label class="form-label">Ghi chú</label>
                <input type="text" class="form-input" id="pt-notes" placeholder="Lý do...">
              </div>
              <button class="btn btn-primary btn-block btn-lg attendance-btn" onclick="handleSubmitPassTime()">
                <i data-lucide="wallet"></i> Gửi Pass Time
              </button>
            </div>
            <div id="passtime-result" class="attendance-result" style="display:none;margin-top:12px"></div>
            <div id="passtime-history" style="margin-top:16px"></div>
          </div>
          <div class="attendance-result" id="att-result"></div>
          <a href="#/attendance/history" class="btn btn-outline btn-block">
            <i data-lucide="history"></i> Xem lịch sử chấm công
          </a>
        </div>
      </div>
      ${renderBottomNav()}
    </div>
  `;
}

async function getEmployeeInfo() {
  try {
    const me = await api.get('/auth/me');
    if (me.employee_id) {
      return await api.get(`/employees/${me.employee_id}`);
    }
  } catch { /* ignore */ }
  return null;
}

let qrScanner = null;
let qrScannerMode = null;

function switchAttTab(tab, btn) {
  document.querySelectorAll('.attendance-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const tabIds = ['att-qrscan-tab', 'att-manual-tab', 'att-checkout-tab', 'att-passtime-tab'];
  tabIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });
  const tabMap = { qrscan: 'att-qrscan-tab', manual: 'att-manual-tab', checkout: 'att-checkout-tab', passtime: 'att-passtime-tab' };
  const showId = tabMap[tab];
  if (showId) {
    const el = document.getElementById(showId);
    if (el) el.classList.remove('hidden');
  }
  document.getElementById('att-result').className = 'attendance-result';
  document.getElementById('att-result').style.display = 'none';

  if (tab === 'qrscan') {
    startQRScan();
  } else {
    stopQRScan();
  }

  if (tab === 'passtime') {
    loadPassTimeHistory();
  }
}

async function startQRScan() {
  const readerEl = document.getElementById('qr-reader');
  const resultEl = document.getElementById('qrscan-result');
  resultEl.className = 'attendance-result';
  resultEl.style.display = 'none';

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    resultEl.className = 'attendance-result error';
    resultEl.style.display = 'block';
    resultEl.innerHTML = `<div class="attendance-result-title">Không hỗ trợ</div><div class="attendance-result-text">Trình duyệt không hỗ trợ camera</div>`;
    return;
  }

  try {
    if (qrScanner) {
      qrScanner.clear();
      qrScanner = null;
    }

    qrScanner = new Html5Qrcode("qr-reader");
    qrScannerMode = 'checkin';

    await qrScanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      async (decodedText) => {
        try {
          const result = document.getElementById('qrscan-result');
          stopQRScan();
          result.className = 'attendance-result';
          result.style.display = 'block';
          result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';

          const parts = decodedText.split(':');

          if (decodedText.startsWith('POS:')) {
            // Máy POS: nhân viên đã đăng nhập → tự động chấm công
            const emp = await getEmployeeInfo();
            const myCode = emp ? emp.employee_code : '';
            if (myCode) {
              try {
                const reveal = await api.post('/attendance/pos-scan-reveal', { qr_data: decodedText });
                const data = await api.post('/attendance/check-in', {
                  qr_data: decodedText,
                  employee_code: myCode,
                  pin_code: reveal.reveal.one_time_pin
                });
                result.className = 'attendance-result success';
                result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
                  <div class="attendance-result-title">Chấm công vào thành công!</div>
                  <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>
                  <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Quét lại</button>`;
                lucide.createIcons();
              } catch (err) {
                result.className = 'attendance-result error';
                result.innerHTML = `<div class="attendance-result-title">Thất bại</div><div class="attendance-result-text">${err.message}</div>
                  <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Thử lại</button>`;
                lucide.createIcons();
              }
              return;
            }
            // Chưa đăng nhập → hiện form nhập tay
            try {
              const reveal = await api.post('/attendance/pos-scan-reveal', { qr_data: decodedText });
              result.innerHTML = `
                <div class="attendance-result-title" style="margin-bottom:12px;color:var(--primary)">
                  <i data-lucide="scan" style="width:16px;height:16px;vertical-align:middle"></i> Đã quét mã POS
                </div>
                <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:10px;margin-bottom:8px;text-align:center">
                  <div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px">Mã nhân viên</div>
                  <div style="font-size:18px;font-weight:700;color:var(--primary)">${reveal.reveal.employee_code_prompt}</div>
                </div>
                <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:10px;margin-bottom:8px;text-align:center">
                  <div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px">Mã PIN 1 lần</div>
                  <div style="font-size:18px;font-weight:700;color:#dc2626;letter-spacing:2px">${reveal.reveal.one_time_pin}</div>
                </div>
                <div class="attendance-input-group">
                  <input type="text" class="form-input" id="pos-scan-emp-code" placeholder="Nhập mã NV" autocomplete="off">
                </div>
                <div class="attendance-input-group">
                  <input type="password" class="form-input" id="pos-scan-pin" placeholder="Nhập mã PIN 1 lần" autocomplete="off">
                </div>
                <button class="btn btn-primary btn-block" onclick="handlePOSScanCheckIn('${decodedText}')" style="margin-top:4px">
                  <i data-lucide="log-in"></i> Chấm vào
                </button>
                <button class="btn btn-outline btn-block" style="margin-top:8px" onclick="resetQRScan()">Huỷ</button>`;
              lucide.createIcons();
            } catch (err) {
              result.className = 'attendance-result error';
              result.innerHTML = `<div class="attendance-result-title">Quét QR thất bại</div><div class="attendance-result-text">${err.message}</div>
                <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Thử lại</button>`;
              lucide.createIcons();
            }
            return;
          }

          if (!decodedText.startsWith('CHAMCONG:')) {
            result.className = 'attendance-result error';
            result.innerHTML = `<div class="attendance-result-title">QR không hợp lệ</div>
              <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Quét lại</button>`;
            lucide.createIcons();
            return;
          }

          // QR cá nhân: chấm công trực tiếp
          const empCode = parts[1];
          try {
            const data = await api.post('/attendance/check-in', { qr_data: decodedText });
            result.className = 'attendance-result success';
            result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
              <div class="attendance-result-title">Chấm công vào thành công!</div>
              <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>
              <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Quét lại</button>`;
            lucide.createIcons();
          } catch (err) {
            result.className = 'attendance-result error';
            result.innerHTML = `<div class="attendance-result-title">Thất bại</div><div class="attendance-result-text">${err.message}</div>
              <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Thử lại</button>`;
            lucide.createIcons();
          }
        } catch (e) {
          showToast('Lỗi xử lý QR', 'error');
        }
      },
      () => {}
    );
  } catch (err) {
    resultEl.className = 'attendance-result error';
    resultEl.style.display = 'block';
    resultEl.innerHTML = `<div class="attendance-result-title">Không thể mở camera</div><div class="attendance-result-text">Vui lòng cấp quyền camera cho trang này</div>`;
  }
}

function stopQRScan() {
  if (qrScanner) {
    qrScanner.stop().catch(() => {});
    qrScanner = null;
  }
}

function resetQRScan() {
  const result = document.getElementById('qrscan-result');
  if (result) {
    result.style.display = 'none';
    result.className = 'attendance-result';
  }
  startQRScan();
}

async function handlePOSScanCheckIn(qrData) {
  const code = document.getElementById('pos-scan-emp-code').value.trim();
  const pin = document.getElementById('pos-scan-pin').value.trim();
  const result = document.getElementById('qrscan-result');
  if (!code || !pin) { showToast('Vui lòng nhập mã NV và mã PIN', 'error'); return; }
  result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';
  try {
    const data = await api.post('/attendance/check-in', { qr_data: qrData, employee_code: code, pin_code: pin });
    result.className = 'attendance-result success';
    result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Chấm vào thành công!</div>
      <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>
      <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Quét lại</button>`;
    lucide.createIcons();
  } catch (err) {
    result.className = 'attendance-result error';
    result.innerHTML = `<div class="attendance-result-title">Thất bại</div><div class="attendance-result-text">${err.message}</div>
      <button class="btn btn-outline btn-block" style="margin-top:12px" onclick="resetQRScan()">Thử lại</button>`;
    lucide.createIcons();
  }
}

async function handleCheckIn() {
  const code = document.getElementById('att-emp-code').value.trim();
  const pin = document.getElementById('att-pin').value.trim();
  const result = document.getElementById('att-result');
  if (!code || !pin) { showToast('Vui lòng nhập mã NV và mã PIN', 'error'); return; }
  result.className = 'attendance-result';
  result.style.display = 'block';
  result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';
  try {
    const data = await api.post('/attendance/check-in', { employee_code: code, pin_code: pin });
    result.className = 'attendance-result success';
    result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Chấm công vào thành công!</div>
      <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>`;
    document.getElementById('att-emp-code').value = '';
    document.getElementById('att-pin').value = '';
  } catch (err) {
    result.className = 'attendance-result error';
    result.innerHTML = `<div class="attendance-result-title" style="color:var(--danger)">Thất bại</div><div class="attendance-result-text">${err.message}</div>`;
  }
}

async function handleCheckOut() {
  const code = document.getElementById('att-emp-code-out').value.trim();
  const result = document.getElementById('att-result');
  if (!code) { showToast('Vui lòng nhập mã NV', 'error'); return; }
  result.className = 'attendance-result';
  result.style.display = 'block';
  result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';
  try {
    const data = await api.post('/attendance/check-out', { employee_code: code });
    result.className = 'attendance-result success';
    result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Chấm công ra thành công!</div>
      <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>`;
    document.getElementById('att-emp-code-out').value = '';
    lucide.createIcons();
  } catch (err) {
    result.className = 'attendance-result error';
    result.innerHTML = `<div class="attendance-result-title" style="color:var(--danger)">Thất bại</div><div class="attendance-result-text">${err.message}</div>`;
  }
}

/* ---------- Employee: Pass Time ---------- */
async function handleSubmitPassTime() {
  const amountEl = document.getElementById('pt-amount');
  const notesEl = document.getElementById('pt-notes');
  const resultEl = document.getElementById('passtime-result');
  const amount = parseFloat(amountEl.value);

  if (!amount || amount <= 0) {
    showToast('Vui lòng nhập số tiền hợp lệ', 'error');
    return;
  }

  resultEl.style.display = 'block';
  resultEl.className = 'attendance-result';
  resultEl.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';

  try {
    await api.post('/attendance/my/pass-time-amount', { amount, notes: notesEl.value });
    resultEl.className = 'attendance-result success';
    resultEl.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Gửi Pass Time thành công!</div>
      <div class="attendance-result-text">${formatCurrency(amount)}</div>`;
    lucide.createIcons();
    amountEl.value = '';
    notesEl.value = '';
    setTimeout(() => loadPassTimeHistory(), 1000);
  } catch (err) {
    resultEl.className = 'attendance-result error';
    resultEl.innerHTML = `<div class="attendance-result-title" style="color:var(--danger)">Thất bại</div><div class="attendance-result-text">${err.message}</div>`;
    lucide.createIcons();
  }
}

async function loadPassTimeHistory() {
  const el = document.getElementById('passtime-history');
  if (!el) return;
  const today = new Date().toISOString().split('T')[0];
  try {
    const records = await api.get(`/attendance/admin/pass-time?date=${today}`);
    if (!records.length) {
      el.innerHTML = '<p style="text-align:center;color:var(--text-secondary);font-size:13px;margin-top:8px">Chưa có pass time hôm nay</p>';
      return;
    }
    const rows = records.map(r => `
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>${r.employee?.full_name || '-'}</span>
        <strong style="color:var(--success)">${formatCurrency(r.pass_time_amount)}</strong>
      </div>
    `).join('');
    el.innerHTML = `<div style="background:var(--bg);border-radius:8px;padding:8px 12px;margin-top:12px">
      <div style="font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">PASS TIME HÔM NAY</div>
      ${rows}
    </div>`;
  } catch {
    el.innerHTML = '<p style="text-align:center;color:var(--text-secondary);font-size:13px;margin-top:8px">Không tải được lịch sử</p>';
  }
}

function updateClock() {
  const el = document.getElementById('current-time');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('vi-VN');
  }
}

/* ============================================
   Page: Attendance History
   ============================================ */
async function renderAttendanceHistory() {
  let records = [];
  try { records = await api.get('/attendance/my?limit=30'); } catch {}
  const rows = records.map(r => `
    <tr>
      <td>${formatDate(r.date)}</td>
      <td>${formatTime(r.check_in)}</td>
      <td>${formatTime(r.check_out)}</td>
      <td>${getStatusBadge(r.status)}</td>
    </tr>
  `).join('');
  return `
    <div class="attendance-page">
      ${renderTopBar('Lịch sử chấm công')}
      <div class="page-content">
        <div class="card">
          <div class="card-header">
            <div><div class="card-title">30 ngày gần nhất</div></div>
          </div>
          <div class="table-wrap">
            ${records.length ? `<table><thead><tr><th>Ngày</th><th>Giờ vào</th><th>Giờ ra</th><th>Trạng thái</th></tr></thead><tbody>${rows}</tbody></table>` : '<div class="empty-state"><p>Chưa có bản ghi chấm công</p></div>'}
          </div>
        </div>
      </div>
      ${renderBottomNav()}
    </div>
  `;
}

/* ============================================
   Page: POS Chấm Công (Máy quét)
   ============================================ */
let posCurrentQR = '';
let posKeyInfo = null;

async function renderPOS() {
  // Lấy thông tin key hôm nay từ server
  let keyData = { date: '', token: '' };
  try {
    keyData = await api.get('/attendance/pos-key-info');
    posKeyInfo = keyData;
    posCurrentQR = keyData.token;
  } catch {
    // fallback
  }

  const todayStr = new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' });

  return `
    <div class="pos-page">
      <div class="pos-header">
        <h2>Chấm Công</h2>
        <p>Máy POS - ${todayStr}</p>
      </div>
      <div class="pos-content">
        <div class="pos-card">
          <div class="pos-qr-wrapper">
            <img id="pos-qr-display" src="${API_BASE}/attendance/pos-qr?cb=${Date.now()}"
                 style="width:200px;height:200px;border-radius:12px;border:3px solid var(--primary)"
                 onload="document.getElementById('pos-qr-placeholder').style.display='none'"
                 onerror="document.getElementById('pos-qr-placeholder').innerHTML='<p style=\\'color:var(--danger);font-size:13px\\'>Không tải được mã QR</p>'">
            <div id="pos-qr-placeholder" class="pos-qr-loading">
              <span class="spinner dark"></span>
              <p>Đang tải mã QR...</p>
            </div>
          </div>
          <p style="font-size:12px;color:var(--text-secondary);margin-top:8px">Quét mã này để bắt đầu chấm công</p>
          <div id="pos-reveal-area" style="display:none;margin-top:12px;padding:16px;background:var(--bg);border-radius:12px;border:2px solid var(--primary)">
            <div style="text-align:center;font-weight:700;font-size:16px;color:var(--primary);margin-bottom:12px">
              <i data-lucide="scan" style="width:18px;height:18px;vertical-align:middle;margin-right:4px"></i>
              Đã quét mã POS
            </div>
            <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:12px;margin-bottom:10px">
              <div style="font-size:12px;color:var(--text-secondary);margin-bottom:4px">Mã nhân viên của bạn</div>
              <div style="font-size:20px;font-weight:700;color:var(--primary);letter-spacing:2px" id="pos-reveal-code">--</div>
            </div>
            <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:12px;margin-bottom:10px">
              <div style="font-size:12px;color:var(--text-secondary);margin-bottom:4px">Mã PIN 1 lần (dùng 1 lần duy nhất)</div>
              <div style="font-size:20px;font-weight:700;color:#dc2626;letter-spacing:3px" id="pos-reveal-pin">------</div>
            </div>
            <div style="font-size:11px;color:var(--text-secondary);text-align:center;padding:8px 0">
              Link đăng nhập: <span style="color:var(--primary);font-weight:600" id="pos-reveal-url">-</span>
            </div>
            <div class="attendance-input-group">
              <label class="form-label">Nhập Mã nhân viên</label>
              <input type="text" class="form-input" id="pos-emp-code" placeholder="VD: NV001" autocomplete="off">
            </div>
            <div class="attendance-input-group">
              <label class="form-label">Nhập Mã PIN 1 lần (bên trên)</label>
              <input type="password" class="form-input" id="pos-pin" placeholder="Nhập mã PIN" autocomplete="off">
            </div>
            <div class="pos-buttons">
              <button class="btn btn-primary btn-lg" onclick="handlePOSCheckIn()">
                <i data-lucide="log-in"></i> Chấm vào
              </button>
              <button class="btn btn-danger btn-lg" onclick="handlePOSCheckOut()">
                <i data-lucide="log-out"></i> Chấm ra
              </button>
            </div>
            <div style="text-align:center;margin-top:8px">
              <button class="btn btn-ghost btn-sm" onclick="hidePOSReveal()">
                <i data-lucide="x"></i> Huỷ
              </button>
            </div>
          </div>
          <div id="pos-input-area">
            <hr class="attendance-divider">
            <div class="attendance-input-group">
              <label class="form-label">Mã nhân viên</label>
              <input type="text" class="form-input" id="pos-emp-code" placeholder="VD: NV001" autocomplete="off">
            </div>
            <div class="attendance-input-group">
              <label class="form-label">Mã PIN</label>
              <input type="password" class="form-input" id="pos-pin" placeholder="Nhập mã PIN" autocomplete="off">
            </div>
            <div class="pos-buttons">
              <button class="btn btn-primary btn-lg" onclick="handlePOSCheckIn()">
                <i data-lucide="log-in"></i> Chấm vào
              </button>
              <button class="btn btn-danger btn-lg" onclick="handlePOSCheckOut()">
                <i data-lucide="log-out"></i> Chấm ra
              </button>
            </div>
          </div>
          <div class="attendance-result" id="pos-result" style="display:none;margin-top:16px;"></div>
        </div>
      </div>
    </div>
  `;
}

async function initPOSScanner() {
  // Khởi tạo quét QR trên trang POS
  const readerEl = document.getElementById('pos-qr-reader');
  if (!readerEl) return;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    return;
  }

  try {
    const scanner = new Html5Qrcode("pos-qr-reader");
    await scanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      async (decodedText) => {
        // Kiểm tra định dạng POS mới
        if (!decodedText.startsWith('POS:')) return;

        // Gọi API reveal để lấy NV + PIN
        try {
          const reveal = await api.post('/attendance/pos-scan-reveal', { qr_data: decodedText });
          posCurrentQR = decodedText;

          document.getElementById('pos-reveal-area').style.display = 'block';
          document.getElementById('pos-input-area').style.display = 'none';
          document.getElementById('pos-reveal-code').textContent = reveal.reveal.employee_code_prompt;
          document.getElementById('pos-reveal-pin').textContent = reveal.reveal.one_time_pin;
          document.getElementById('pos-reveal-url').textContent = reveal.reveal.login_url;
          lucide.createIcons();

          await scanner.stop();
        } catch (err) {
          showToast(err.message, 'error');
        }
      },
      () => {}
    );
    window._posScanner = scanner;
  } catch (err) {
    // Scanner not available on this device
  }
}

function hidePOSReveal() {
  document.getElementById('pos-reveal-area').style.display = 'none';
  document.getElementById('pos-input-area').style.display = 'block';
  // Restart scanner
  if (window._posScanner) {
    window._posScanner.stop().catch(() => {});
    delete window._posScanner;
  }
  setTimeout(() => initPOSScanner(), 500);
}

async function handlePOSCheckIn() {
  const code = document.getElementById('pos-emp-code').value.trim();
  const pin = document.getElementById('pos-pin').value.trim();
  const result = document.getElementById('pos-result');
  if (!code || !pin) { showToast('Vui lòng nhập mã NV và mã PIN', 'error'); return; }
  result.className = 'attendance-result';
  result.style.display = 'block';
  result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';
  try {
    const data = await api.post('/attendance/check-in', {
      qr_data: posCurrentQR || undefined,
      employee_code: code,
      pin_code: pin
    });
    result.className = 'attendance-result success';
    result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Chấm vào thành công!</div>
      <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>`;
    document.getElementById('pos-emp-code').value = '';
    document.getElementById('pos-pin').value = '';
    lucide.createIcons();
  } catch (err) {
    result.className = 'attendance-result error';
    result.innerHTML = `<div class="attendance-result-title" style="color:var(--danger)">Thất bại</div><div class="attendance-result-text">${err.message}</div>`;
  }
}

async function handlePOSCheckOut() {
  const code = document.getElementById('pos-emp-code').value.trim();
  const pin = document.getElementById('pos-pin').value.trim();
  const result = document.getElementById('pos-result');
  if (!code || !pin) { showToast('Vui lòng nhập mã NV và mã PIN', 'error'); return; }
  result.className = 'attendance-result';
  result.style.display = 'block';
  result.innerHTML = '<div class="text-center"><span class="spinner dark"></span></div>';
  try {
    const data = await api.post('/attendance/check-out', {
      qr_data: posCurrentQR || undefined,
      employee_code: code,
      pin_code: pin
    });
    result.className = 'attendance-result success';
    result.innerHTML = `<div class="check-animation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
      <div class="attendance-result-title">Chấm ra thành công!</div>
      <div class="attendance-result-text">${data.employee_name} - ${formatTime(data.time)}</div>`;
    document.getElementById('pos-emp-code').value = '';
    document.getElementById('pos-pin').value = '';
    lucide.createIcons();
  } catch (err) {
    result.className = 'attendance-result error';
    result.innerHTML = `<div class="attendance-result-title" style="color:var(--danger)">Thất bại</div><div class="attendance-result-text">${err.message}</div>`;
  }
}

/* ============================================
   Shared: Bottom Nav (Mobile)
   ============================================ */
function renderBottomNav() {
  return `
    <div style="position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--border);display:flex;z-index:50;padding-bottom:env(safe-area-inset-bottom)">
      <a href="#/attendance" class="bottom-nav-item" onclick="render()">
        <i data-lucide="clock"></i><span>Chấm công</span>
      </a>
      <a href="#/attendance/history" class="bottom-nav-item" onclick="render()">
        <i data-lucide="history"></i><span>Lịch sử</span>
      </a>
      <button class="bottom-nav-item" onclick="api.logout(); navigate('/login'); render();">
        <i data-lucide="log-out"></i><span>Đăng xuất</span>
      </button>
    </div>
    <style>
      .bottom-nav-item { flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; padding:12px 8px; border:none; background:none; cursor:pointer; color:var(--text-secondary); text-decoration:none; font-size:11px; font-weight:500; transition:color 0.15s; }
      .bottom-nav-item:hover, .bottom-nav-item:focus { color:var(--primary); }
      .bottom-nav-item svg { width:20px; height:20px; stroke:currentColor; stroke-width:2; fill:none; }
    </style>
  `;
}

/* ============================================
   Admin Layout
   ============================================ */
function renderAdminLayout(pageTitle, content) {
  const role = api.role;
  return `
    <div class="app-layout">
      ${renderSidebar(role)}
      <div class="main-content">
        ${renderMainHeader(pageTitle)}
        <div class="page-content">${content}</div>
      </div>
    </div>
  `;
}

function renderSidebar(role) {
  const navItems = [
    { path: '/admin', icon: 'layout-dashboard', label: 'Tổng quan', roles: ['admin', 'manager'] },
    { path: '/admin/employees', icon: 'users', label: 'Nhân viên', roles: ['admin'] },
    { path: '/admin/attendance', icon: 'calendar-check', label: 'Chấm công', roles: ['admin', 'manager'] },
    { path: '/admin/salary', icon: 'wallet', label: 'Lương', roles: ['admin', 'manager'] },
    { path: '#reset-pos', icon: 'refresh-cw', label: 'Reset POS', roles: ['admin', 'manager'], action: 'openAdminResetPOS' },
    { path: '#pass-time', icon: 'clock', label: 'Part Time', roles: ['admin', 'manager'], action: 'openAdminPartTime' },
    { path: '#add-att', icon: 'plus-circle', label: 'Thêm giờ', roles: ['admin', 'manager'], action: 'openAdminAddAttendance' },
  ].filter(n => n.roles.includes(role));

  const items = navItems.map(n => {
    const isActive = currentRoute === n.path || (n.path !== '#' && currentRoute.startsWith(n.path + '/'));
    if (n.action) {
      return `<a href="#/admin/attendance" class="nav-item ${isActive ? 'active' : ''}" onclick="setTimeout(() => ${n.action}(), 100)">
        <i data-lucide="${n.icon}"></i>${n.label}
      </a>`;
    }
    return `<a href="#${n.path}" class="nav-item ${isActive ? 'active' : ''}" onclick="render()">
      <i data-lucide="${n.icon}"></i>${n.label}
    </a>`;
  }).join('');

  return `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">CC</div>
        <div>
          <div class="sidebar-logo-text">Chấm Công</div>
          <div class="sidebar-logo-sub">Thông Minh</div>
        </div>
      </div>
      <nav class="sidebar-nav">${items}</nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">${(api.username || 'A').charAt(0).toUpperCase()}</div>
          <div>
            <div class="user-name">${api.username}</div>
            <div class="user-role">${role === 'admin' ? 'Quản trị' : 'Quản lý'}</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-block mt-2" onclick="api.logout(); navigate('/login'); render();">
          <i data-lucide="log-out"></i> Đăng xuất
        </button>
      </div>
    </aside>
    <button class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')" style="position:fixed;top:12px;left:12px;z-index:200;display:none">
      <i data-lucide="menu"></i>
    </button>
  `;
}

function renderMainHeader(title) {
  return `
    <header class="main-header">
      <button class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">
        <i data-lucide="menu"></i>
      </button>
      <h1 class="main-header-title">${title}</h1>
      <div class="main-header-actions">
        <span class="text-muted" style="font-size:13px">${new Date().toLocaleDateString('vi-VN')}</span>
      </div>
    </header>
  `;
}

function renderTopBar(title) {
  return `
    <div style="background:var(--primary);color:#fff;padding:20px 16px 24px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <a href="#/attendance" style="color:#fff"><i data-lucide="arrow-left" style="width:20px;height:20px;stroke:#fff"></i></a>
        <h2 style="font-size:20px;font-weight:700">${title}</h2>
      </div>
    </div>
  `;
}

/* ============================================
   Admin: Dashboard
   ============================================ */
async function renderAdminDashboard() {
  let stats = { total_employees: 0, total_records: 0, present: 0, late: 0, early_leave: 0, absent: 0, on_time_rate: 0 };
  let trend = { trend: [] };
  try { stats = await api.get('/reports/summary'); } catch {}
  try { trend = await api.get('/reports/trend?months=6'); } catch {}

  return renderAdminLayout('Tổng quan', `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:#DBEAFE"><i data-lucide="users" style="width:22px;height:22px;stroke:#2563EB;fill:none"></i></div>
        <div class="stat-value">${stats.total_employees || 0}</div>
        <div class="stat-label">Tổng nhân viên</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#D1FAE5"><i data-lucide="check-circle" style="width:22px;height:22px;stroke:#10B981;fill:none"></i></div>
        <div class="stat-value">${stats.present || 0}</div>
        <div class="stat-label">Có mặt (30 ngày)</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#FEF3C7"><i data-lucide="clock" style="width:22px;height:22px;stroke:#F59E0B;fill:none"></i></div>
        <div class="stat-value">${stats.late || 0}</div>
        <div class="stat-label">Đi muộn</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#FEE2E2"><i data-lucide="x-circle" style="width:22px;height:22px;stroke:#EF4444;fill:none"></i></div>
        <div class="stat-value">${stats.absent || 0}</div>
        <div class="stat-label">Vắng mặt</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">Xu hướng chấm công</div>
      </div>
      <div class="chart-container">
        <canvas id="trendChart"></canvas>
      </div>
    </div>
  `);
}

/* ============================================
   Admin: Employees
   ============================================ */
let employeesData = [];
let departmentsData = [];

async function renderAdminEmployees() {
  try { employeesData = await api.get('/employees'); } catch {}
  try { departmentsData = await api.get('/employees/departments'); } catch {}

  return renderAdminLayout('Quản lý Nhân viên', `
    <div class="card">
      <div class="card-header">
        <div class="search-bar">
          <div class="search-input-wrap">
            <i data-lucide="search"></i>
            <input type="text" class="search-input" placeholder="Tìm tên, mã NV..." id="emp-search" oninput="filterEmployees()">
          </div>
        </div>
        <button class="btn btn-primary" onclick="openAddEmployee()">
          <i data-lucide="plus"></i> Them nhan vien
        </button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Ma NV</th><th>Ho ten</th><th>Loai</th><th>Luong CB</th><th>Luong/gio</th><th style="text-align:right">Thao tac</th></tr></thead>
          <tbody id="emp-table-body">${renderEmployeeRows(employeesData)}</tbody>
        </table>
      </div>
      ${employeesData.length === 0 ? '<div class="empty-state"><h3>Chưa có nhân viên</h3><p>Thêm nhân viên đầu tiên</p></div>' : ''}
    </div>
  `);
}

function renderEmployeeRows(emps) {
  return emps.map(e => {
    const isPT = e.employee_type === 'parttime';
    const typeLabel = isPT
      ? '<span class="badge" style="background:#7c3aed;color:#fff">Part Time</span>'
      : '<span class="badge badge-info">Full Time</span>';
    return `<tr>
      <td><span class="badge badge-info">${e.employee_code}</span></td>
      <td><strong>${e.full_name}</strong></td>
      <td>${typeLabel}</td>
      <td>${isPT ? '-' : formatCurrency(e.base_salary)}</td>
      <td>${isPT ? formatCurrency(e.hourly_rate) + '/gio' : '-'}</td>
      <td style="text-align:right">
        <button class="btn btn-ghost btn-sm" onclick="viewEmployeeQR(${e.id})" title="Xem QR"><i data-lucide="qr-code"></i></button>
        <button class="btn btn-ghost btn-sm" onclick="editEmployee(${e.id})"><i data-lucide="pencil"></i></button>
        <button class="btn btn-ghost btn-sm" onclick="deleteEmployee(${e.id})"><i data-lucide="trash-2" style="stroke:var(--danger)"></i></button>
      </td>
    </tr>`;
  }).join('');
}

function filterEmployees() {
  const q = document.getElementById('emp-search').value.toLowerCase();
  const filtered = employeesData.filter(e =>
    e.full_name.toLowerCase().includes(q) || e.employee_code.toLowerCase().includes(q) || (e.department || '').toLowerCase().includes(q)
  );
  document.getElementById('emp-table-body').innerHTML = renderEmployeeRows(filtered);
  lucide.createIcons();
}

function openAddEmployee() {
  openModal('Them nhan vien', `
    <form id="emp-form" onsubmit="saveEmployee(event)">
      <div class="form-row">
        <div class="form-group"><label class="form-label">Ma nhan vien *</label><input type="text" class="form-input" id="emp-code" required placeholder="NV001"></div>
        <div class="form-group"><label class="form-label">Ma PIN *</label><input type="text" class="form-input" id="emp-pin" required placeholder="1234" maxlength="6"></div>
      </div>
      <div class="form-group"><label class="form-label">Ho ten *</label><input type="text" class="form-input" id="emp-name" required placeholder="Nguyen Van A"></div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">Phong ban *</label>
          <select class="form-select" id="emp-dept" required>
            <option value="">-- Chon --</option>
            <option value="Ky thuat">Ky thuat</option>
            <option value="Kinh doanh">Kinh doanh</option>
            <option value="Nhan su">Nhan su</option>
            <option value="Tai chinh">Tai chinh</option>
            <option value="Marketing">Marketing</option>
            <option value="Van hanh">Van hanh</option>
          </select>
        </div>
        <div class="form-group"><label class="form-label">Chuc vu *</label><input type="text" class="form-input" id="emp-pos" required placeholder="Nhan vien"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">Email</label><input type="email" class="form-input" id="emp-email" placeholder="email@example.com"></div>
        <div class="form-group"><label class="form-label">SDT</label><input type="text" class="form-input" id="emp-phone" placeholder="0xxx"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">Loai nhan vien</label>
          <select class="form-select" id="emp-type" onchange="toggleSalaryFields()">
            <option value="fulltime">Full Time</option>
            <option value="parttime">Part Time (Sinh vien)</option>
          </select>
        </div>
        <div class="form-group" id="fg-salary"><label class="form-label">Luong co ban</label><input type="number" class="form-input" id="emp-salary" placeholder="5000000" min="0"></div>
      </div>
      <div class="form-group" id="fg-hourly" style="display:none">
        <label class="form-label">Luong moi gio (VNĐ)</label><input type="number" class="form-input" id="emp-hourly" placeholder="25000" min="0" step="1000">
      </div>
      <input type="hidden" id="emp-id" value="">
    </form>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Huy</button>
    <button class="btn btn-primary" onclick="document.getElementById('emp-form').dispatchEvent(new Event('submit'))">Luu</button>
  `);
}

function toggleSalaryFields() {
  const type = document.getElementById('emp-type').value;
  const fgSalary = document.getElementById('fg-salary');
  const fgHourly = document.getElementById('fg-hourly');
  if (type === 'parttime') {
    fgSalary.style.display = 'none';
    fgHourly.style.display = 'block';
  } else {
    fgSalary.style.display = 'block';
    fgHourly.style.display = 'none';
  }
}

async function saveEmployee(e) {
  e.preventDefault();
  const id = document.getElementById('emp-id').value;
  const empType = document.getElementById('emp-type').value;
  const data = {
    employee_code: document.getElementById('emp-code').value,
    pin_code: document.getElementById('emp-pin').value,
    full_name: document.getElementById('emp-name').value,
    department: document.getElementById('emp-dept').value,
    position: document.getElementById('emp-pos').value,
    email: document.getElementById('emp-email').value || null,
    phone: document.getElementById('emp-phone').value || null,
    base_salary: empType === 'fulltime' ? (parseFloat(document.getElementById('emp-salary').value) || 0) : 0,
    employee_type: empType,
    hourly_rate: empType === 'parttime' ? (parseFloat(document.getElementById('emp-hourly').value) || 0) : 0,
    password: '123456',
  };
  try {
    if (id) {
      await api.put(`/employees/${id}`, data);
      showToast('Cap nhat thanh cong!');
    } else {
      await api.post('/employees', data);
      showToast('Them nhan vien thanh cong!');
    }
    closeModal();
    render();
  } catch (err) { showToast(err.message, 'error'); }
}

async function editEmployee(id) {
  const emp = employeesData.find(e => e.id === id);
  if (!emp) return;
  openAddEmployee();
  setTimeout(() => {
    document.getElementById('emp-id').value = emp.id;
    document.getElementById('emp-code').value = emp.employee_code;
    document.getElementById('emp-code').disabled = true;
    document.getElementById('emp-pin').value = '';
    document.getElementById('emp-pin').placeholder = 'De trong neu khong doi';
    document.getElementById('emp-name').value = emp.full_name;
    document.getElementById('emp-dept').value = emp.department;
    document.getElementById('emp-pos').value = emp.position;
    document.getElementById('emp-email').value = emp.email || '';
    document.getElementById('emp-phone').value = emp.phone || '';
    const empType = emp.employee_type || 'fulltime';
    document.getElementById('emp-type').value = empType;
    document.getElementById('emp-salary').value = empType === 'fulltime' ? (emp.base_salary || 0) : 0;
    document.getElementById('emp-hourly').value = empType === 'parttime' ? (emp.hourly_rate || 0) : 0;
    toggleSalaryFields();
  }, 100);
}

async function deleteEmployee(id) {
  if (!confirm('Ban co chan xoa nhan vien nay?')) return;
  try {
    await api.del(`/employees/${id}`);
    showToast('Xoa thanh cong!');
    render();
  } catch (err) { showToast(err.message || 'Xoa that bai', 'error'); }
}

async function viewEmployeeQR(id) {
  const emp = employeesData.find(e => e.id === id);
  if (!emp) return;
  const qrUrl = `${API_BASE}/employees/${id}/qr-code`;
  openModal(`QR Code - ${emp.full_name}`, `
    <div class="text-center">
      <img src="${qrUrl}" style="width:200px;height:200px;border-radius:8px;margin-bottom:12px" alt="QR Code">
      <p style="font-size:13px;color:var(--text-secondary)">Mã NV: <strong>${emp.employee_code}</strong></p>
      <p style="font-size:12px;color:var(--text-secondary);margin-top:4px">Quét mã này để chấm công</p>
    </div>
  `, `<button class="btn btn-primary" onclick="closeModal()">Đóng</button>`);
}

/* ============================================
   Admin: Attendance
   ============================================ */
let attendanceData = [];

async function renderAdminAttendance() {
  const today = new Date().toISOString().split('T')[0];
  try {
    attendanceData = await api.get(`/attendance?date_from=${today}&date_to=${today}&limit=100`);
  } catch {}
  return renderAdminLayout('Bảng Chấm Công', `
    <div class="card" style="margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 16px;background:var(--bg);border-radius:var(--radius)">
        <div class="filter-group">
          <label class="filter-label">Từ ngày</label>
          <input type="date" class="form-input" id="att-date-from" value="${today}" style="width:140px">
        </div>
        <div class="filter-group">
          <label class="filter-label">Đến ngày</label>
          <input type="date" class="form-input" id="att-date-to" value="${today}" style="width:140px">
        </div>
        <button class="btn btn-primary btn-sm" onclick="loadAttendance()">
          <i data-lucide="search"></i> Lọc
        </button>
        <div style="flex:1"></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-outline btn-sm" onclick="openAdminResetPOS()" title="Reset mã POS">
            <i data-lucide="refresh-cw"></i> Reset POS
          </button>
          <button class="btn btn-outline btn-sm" onclick="openAdminAddAttendance()" title="Thêm bản ghi chấm công">
            <i data-lucide="plus-circle"></i> Thêm giờ
          </button>
          <button class="btn btn-outline btn-sm" onclick="openAdminPartTime()" title="Quản lý Part Time">
            <i data-lucide="clock"></i> Part Time
          </button>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Ngày</th><th>Mã NV</th><th>Họ tên</th><th>Phòng ban</th><th>Giờ vào</th><th>Giờ ra</th><th>Pass Time</th><th>Trạng thái</th><th style="text-align:right">Thao tác</th></tr></thead>
          <tbody id="att-table-body">${renderAttendanceRows(attendanceData)}</tbody>
        </table>
      </div>
      ${attendanceData.length === 0 ? '<div class="empty-state"><h3>Không có dữ liệu</h3><p>Không có bản ghi nào trong khoảng thời gian này</p></div>' : ''}
    </div>
  `);
}

function renderAttendanceRows(records) {
  return records.map(r => `
    <tr>
      <td>${formatDate(r.date)}</td>
      <td><span class="badge badge-info">${r.employee?.employee_code || ''}</span></td>
      <td>${r.employee?.full_name || '-'}</td>
      <td>${r.employee?.department || '-'}</td>
      <td>${formatTime(r.check_in)}</td>
      <td>${formatTime(r.check_out)}</td>
      <td>${r.pass_time_amount ? formatCurrency(r.pass_time_amount) : '-'}</td>
      <td>${getStatusBadge(r.status)}</td>
      <td style="text-align:right">
        <button class="btn btn-ghost btn-sm" onclick="openAdminEditAttendance(${r.id})" title="Sửa giờ"><i data-lucide="pencil"></i></button>
      </td>
    </tr>
  `).join('');
}

async function loadAttendance() {
  const from = document.getElementById('att-date-from').value;
  const to = document.getElementById('att-date-to').value;
  try {
    attendanceData = await api.get(`/attendance?date_from=${from}&date_to=${to}&limit=500`);
    document.getElementById('att-table-body').innerHTML = renderAttendanceRows(attendanceData);
    lucide.createIcons();
  } catch (err) { showToast(err.message, 'error'); }
}

/* ---------- Admin: Reset POS ---------- */
async function openAdminResetPOS() {
  const today = new Date().toISOString().split('T')[0];
  let keyInfo = '';
  try {
    const info = await api.get('/attendance/pos-key-info');
    keyInfo = info.used
      ? `<div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;padding:10px;margin-bottom:12px;text-align:center">
           <div style="font-size:12px;color:#991b1b;margin-bottom:4px">Trạng thái hôm nay</div>
           <div style="font-size:16px;font-weight:700;color:#991b1b">Mã đã bị reset hết lượt</div>
         </div>`
      : `<div style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:8px;padding:10px;margin-bottom:12px;text-align:center">
           <div style="font-size:12px;color:#065f46;margin-bottom:4px">Trạng thái hôm nay</div>
           <div style="font-size:16px;font-weight:700;color:#065f46">Mã còn hoạt động</div>
         </div>`;
  } catch {}

  openModal('Reset mã POS', `
    <div style="margin-bottom:12px">${keyInfo}
      <div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">Chọn ngày cần reset (để trống = hôm nay)</div>
      <input type="date" class="form-input" id="pos-reset-date" value="${today}" style="margin-bottom:12px">
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Đóng</button>
    <button class="btn btn-warning" onclick="doAdminReopenPOS()"><i data-lucide="unlock"></i> Mở lại mã cũ</button>
    <button class="btn btn-primary" onclick="doAdminRegeneratePOS()"><i data-lucide="refresh-cw"></i> Tạo mã mới</button>
  `);
}

async function doAdminRegeneratePOS() {
  try {
    const dateStr = document.getElementById('pos-reset-date').value;
    const query = dateStr ? `?date_str=${dateStr}&action=regenerate` : '?action=regenerate';
    const res = await api.post(`/attendance/admin/pos-reset${query}`);
    closeModal();
    showToast('Đã tạo mã POS mới!');
  } catch (err) { showToast(err.message, 'error'); }
}

async function doAdminReopenPOS() {
  try {
    const dateStr = document.getElementById('pos-reset-date').value;
    const query = dateStr ? `?date_str=${dateStr}&action=reopen` : '?action=reopen';
    const res = await api.post(`/attendance/admin/pos-reset${query}`);
    closeModal();
    showToast('Đã mở lại mã POS!');
  } catch (err) { showToast(err.message, 'error'); }
}

/* ---------- Admin: Add Attendance ---------- */
async function openAdminAddAttendance() {
  let emps = [];
  try { emps = await api.get('/employees'); } catch {}

  const empOptions = emps.map(e => `<option value="${e.id}">${e.employee_code} - ${e.full_name}</option>`).join('');
  openModal('Thêm bản ghi chấm công', `
    <form id="admin-add-att-form" onsubmit="doAdminAddAttendance(event)">
      <div class="form-group">
        <label class="form-label">Nhân viên *</label>
        <select class="form-select" id="add-att-emp" required>
          <option value="">-- Chọn nhân viên --</option>
          ${empOptions}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Ngày *</label>
        <input type="date" class="form-input" id="add-att-date" value="${new Date().toISOString().split('T')[0]}" required>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Giờ vào</label>
          <input type="time" class="form-input" id="add-att-in" value="08:00">
        </div>
        <div class="form-group">
          <label class="form-label">Giờ ra</label>
          <input type="time" class="form-input" id="add-att-out" value="17:00">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Ghi chú</label>
        <input type="text" class="form-input" id="add-att-notes" placeholder="Lý do thêm bản ghi...">
      </div>
    </form>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Hủy</button>
    <button class="btn btn-primary" onclick="document.getElementById('admin-add-att-form').dispatchEvent(new Event('submit'))">Lưu</button>
  `);
}

async function doAdminAddAttendance(e) {
  e.preventDefault();
  const empId = document.getElementById('add-att-emp').value;
  const dateStr = document.getElementById('add-att-date').value;
  const timeIn = document.getElementById('add-att-in').value;
  const timeOut = document.getElementById('add-att-out').value;
  const notes = document.getElementById('add-att-notes').value;

  const checkIn = timeIn ? `${dateStr}T${timeIn}:00` : null;
  const checkOut = timeOut ? `${dateStr}T${timeOut}:00` : null;

  try {
    await api.post('/attendance/admin/attendance', {
      employee_id: parseInt(empId),
      date: dateStr,
      check_in: checkIn,
      check_out: checkOut,
      notes: notes
    });
    closeModal();
    showToast('Đã thêm bản ghi chấm công!');
    loadAttendance();
  } catch (err) { showToast(err.message, 'error'); }
}

/* ---------- Admin: Edit Attendance ---------- */
async function openAdminEditAttendance(recordId) {
  const rec = attendanceData.find(r => r.id === recordId);
  if (!rec) return;

  const dateStr = rec.date;
  const formatTimeInput = (dt) => {
    if (!dt) return '';
    const d = new Date(dt);
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  };

  openModal('Sửa bản ghi chấm công', `
    <form id="admin-edit-att-form" onsubmit="doAdminEditAttendance(event, ${recordId})">
      <div style="background:var(--bg);border-radius:8px;padding:12px;margin-bottom:12px;font-size:13px">
        <div><strong>${rec.employee?.full_name || '-'}</strong> — ${formatDate(dateStr)}</div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Giờ vào</label>
          <input type="time" class="form-input" id="edit-att-in" value="${formatTimeInput(rec.check_in)}">
        </div>
        <div class="form-group">
          <label class="form-label">Giờ ra</label>
          <input type="time" class="form-input" id="edit-att-out" value="${formatTimeInput(rec.check_out)}">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Ghi chú</label>
        <input type="text" class="form-input" id="edit-att-notes" value="${rec.notes || ''}" placeholder="Ghi chú...">
      </div>
    </form>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Hủy</button>
    <button class="btn btn-primary" onclick="document.getElementById('admin-edit-att-form').dispatchEvent(new Event('submit'))">Lưu</button>
  `);
}

async function doAdminEditAttendance(e, recordId) {
  e.preventDefault();
  const rec = attendanceData.find(r => r.id === recordId);
  const dateStr = rec.date;
  const timeIn = document.getElementById('edit-att-in').value;
  const timeOut = document.getElementById('edit-att-out').value;
  const notes = document.getElementById('edit-att-notes').value;

  const checkIn = timeIn ? `${dateStr}T${timeIn}:00` : null;
  const checkOut = timeOut ? `${dateStr}T${timeOut}:00` : null;

  try {
    await api.put(`/attendance/admin/attendance/${recordId}`, {
      check_in: checkIn,
      check_out: checkOut,
      notes: notes
    });
    closeModal();
    showToast('Đã cập nhật bản ghi!');
    loadAttendance();
  } catch (err) { showToast(err.message, 'error'); }
}

/* ---------- Admin: Pass Time ---------- */
let passTimeData = [];

async function openAdminPartTime() {
  const today = new Date().toISOString().split('T')[0];
  try {
    partTimeData = await api.get(`/attendance/admin/part-time?date=${today}`);
  } catch { partTimeData = []; }
  renderPartTimeTable(partTimeData);
  openModal('Quan ly Part Time (Sinh vien)', `
    <div style="margin-bottom:12px">
      <div class="filter-group" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <label class="filter-label">Ngay</label>
        <input type="date" class="form-input" id="pt-date" value="${today}" style="width:150px" onchange="loadPartTimeData()">
        <span style="color:var(--text-secondary);font-size:12px;margin-left:8px">
          Nhan vien <strong>Part Time</strong> da cham cong ngay nay
        </span>
      </div>
    </div>
    <div class="table-wrap" style="max-height:400px;overflow-y:auto">
      <table>
        <thead><tr><th>Ma NV</th><th>Ho ten</th><th>Phong ban</th><th>So tien (VNĐ)</th><th>Ghi chu</th></tr></thead>
        <tbody id="pt-table-body"></tbody>
      </table>
    </div>
  `, `<button class="btn btn-primary" onclick="closeModal()">Dong</button>`);
  renderPartTimeTable(partTimeData);
}

function renderPartTimeTable(data) {
  if (!data || data.length === 0) {
    document.getElementById('pt-table-body').innerHTML =
      '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary);padding:24px">Chua co nhan vien Part Time cham cong ngay nay</td></tr>';
    return;
  }
  const rows = data.map(r => `
    <tr>
      <td><span class="badge badge-info">${r.employee?.employee_code || ''}</span></td>
      <td>${r.employee?.full_name || '-'}</td>
      <td>${r.employee?.department || '-'}</td>
      <td>
        <input type="number" class="form-input" value="${r.pass_time_amount || ''}" min="0" step="1000" id="pt-amount-${r.id}"
          style="width:140px" placeholder="Nhap so tien" onchange="updatePartTimeAmount(${r.id})">
      </td>
      <td><span style="color:var(--text-secondary);font-size:12px">${r.notes || ''}</span></td>
    </tr>`).join('');
  document.getElementById('pt-table-body').innerHTML = rows;
}

async function loadPartTimeData() {
  const dateStr = document.getElementById('pt-date').value;
  try {
    partTimeData = await api.get(`/attendance/admin/part-time?date=${dateStr}`);
  } catch { partTimeData = []; }
  renderPartTimeTable(partTimeData);
}

async function updatePartTimeAmount(recordId) {
  const amount = parseFloat(document.getElementById('pt-amount-' + recordId).value) || 0;
  try {
    await api.put(`/attendance/admin/part-time/${recordId}`, { amount: amount });
    showToast('Da cap nhat so tien Part Time!');
  } catch {
    showToast('Khong the cap nhat', 'error');
  }
}

/* ============================================
   Admin: Salary
   ============================================ */
let salaryData = [];

async function renderAdminSalary() {
  const now = new Date();
  const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  try {
    salaryData = await api.get(`/salary?month=${currentMonth}`);
  } catch {}

  return renderAdminLayout('Bảng Lương', `
    <div class="card">
      <div class="card-header">
        <div class="filter-bar" style="padding:0;border:none;margin:0">
          <div class="filter-group">
            <label class="filter-label">Tháng</label>
            <input type="month" class="form-input" id="salary-month" value="${currentMonth}" style="width:160px">
          </div>
          <button class="btn btn-primary btn-sm" onclick="loadSalary()">
            <i data-lucide="calculator"></i> Tính lương
          </button>
          <button class="btn btn-outline btn-sm" onclick="exportSalary()">
            <i data-lucide="download"></i> Xuất Excel
          </button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Mã NV</th><th>Họ tên</th><th>Phòng ban</th><th>Loại</th><th>Ngày/Giờ</th><th>Lương CB</th><th>Phụ cấp</th><th>Trừ đi muộn</th><th>Trừ vắng</th><th>Thực nhận</th><th>Trạng thái</th></tr></thead>
          <tbody id="salary-table-body">${renderSalaryRows(salaryData)}</tbody>
        </table>
      </div>
      ${salaryData.length === 0 ? '<div class="empty-state"><h3>Chưa có dữ liệu lương</h3><p>Nhấn "Tính lương" để tạo bảng lương tháng này</p></div>' : ''}
    </div>
  `);
}

function renderSalaryRows(records) {
  return records.map(r => {
    const empType = r.employee?.employee_type || 'fulltime';
    const isPartTime = empType === 'parttime';
    const typeLabel = isPartTime
      ? '<span class="badge" style="background:#7c3aed;color:#fff">Part Time</span>'
      : '<span class="badge badge-info">Full Time</span>';
    const dayHours = isPartTime ? `${r.actual_days} giờ` : `${r.actual_days}/${r.working_days} ngày`;
    return `<tr>
      <td><span class="badge badge-info">${r.employee?.employee_code || ''}</span></td>
      <td><strong>${r.employee?.full_name || '-'}</strong></td>
      <td>${r.employee?.department || '-'}</td>
      <td>${typeLabel}</td>
      <td>${dayHours}</td>
      <td>${isPartTime ? '<span style="color:var(--text-secondary)">Tien da nhap</span>' : formatCurrency(r.base_salary)}</td>
      <td class="text-success">+${formatCurrency(r.allowances)}</td>
      <td class="text-danger">-${formatCurrency(r.late_deduction)}</td>
      <td class="text-danger">-${formatCurrency(r.absent_deduction)}</td>
      <td><strong>${formatCurrency(r.net_salary)}</strong></td>
      <td>${getStatusBadge(r.status)}</td>
    </tr>`;
  }).join('');
}

async function loadSalary() {
  const month = document.getElementById('salary-month').value;
  if (!month) return;
  try {
    showToast('Đang tính lương...', 'warning');
    salaryData = await api.post(`/salary/calculate/${month}`);
    document.getElementById('salary-table-body').innerHTML = renderSalaryRows(salaryData);
    showToast('Tính lương thành công!');
  } catch (err) { showToast(err.message, 'error'); }
}

function exportSalary() {
  if (salaryData.length === 0) { showToast('Chưa có dữ liệu để xuất', 'error'); return; }
  const headers = ['Mã NV', 'Họ tên', 'Phòng ban', 'Loại', 'Ngày/Giờ', 'Lương CB', 'Phụ cấp', 'Trừ đi muộn', 'Trừ vắng', 'Thực nhận', 'Trạng thái'];
  const rows = salaryData.map(r => {
    const empType = r.employee?.employee_type || 'fulltime';
    const isPartTime = empType === 'parttime';
    const dayHours = isPartTime ? `${r.actual_days} giờ` : `${r.actual_days}/${r.working_days} ngày`;
    return [
      r.employee?.employee_code || '', r.employee?.full_name || '', r.employee?.department || '',
      isPartTime ? 'Part Time' : 'Full Time',
      dayHours,
      r.base_salary, r.allowances, r.late_deduction, r.absent_deduction, r.net_salary, r.status
    ];
  });
  downloadCSV([headers, ...rows], `bang_luong_${document.getElementById('salary-month').value}.csv`);
  showToast('Đã xuất file CSV!');
}

function downloadCSV(data, filename) {
  const csv = data.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/* ============================================
   Main Render
   ============================================ */
async function render() {
  const route = getRoute();
  currentRoute = route;
  const app = document.getElementById('app');

  switch (routes[route]) {
    case 'login':
      app.innerHTML = renderLogin();
      break;
    case 'attendance':
      app.innerHTML = await renderAttendance();
      lucide.createIcons();
      setInterval(updateClock, 1000);
      updateClock();
      startQRScan();
      break;
    case 'attendance-history':
      app.innerHTML = await renderAttendanceHistory();
      break;
    case 'admin':
      app.innerHTML = await renderAdminDashboard();
      initTrendChart();
      break;
    case 'admin-employees':
      app.innerHTML = await renderAdminEmployees();
      break;
    case 'admin-attendance':
      app.innerHTML = await renderAdminAttendance();
      break;
    case 'admin-salary':
      app.innerHTML = await renderAdminSalary();
      break;
    case 'pos':
      app.innerHTML = await renderPOS();
      lucide.createIcons();
      break;
    default:
      navigate('/login');
      return;
  }

  lucide.createIcons();
}

async function initTrendChart() {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;
  try {
    const data = await api.get('/reports/trend?months=6');
    const labels = data.trend.map(t => t.month);
    const onTime = data.trend.map(t => t.on_time_rate);
    const late = data.trend.map(t => t.late);

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Tỷ lệ đúng giờ (%)', data: onTime, backgroundColor: '#10B981' },
          { label: 'Số lần đi muộn', data: late, backgroundColor: '#F59E0B', yAxisID: 'y1' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: {
          y: { type: 'linear', position: 'left', max: 100, title: { display: true, text: '%' } },
          y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false } }
        }
      }
    });
  } catch { /* chart not available */ }
}

/* ============================================
   Boot
   ============================================ */
document.addEventListener('DOMContentLoaded', () => {
  render();
});
