/* ════════════════════════════════════════════════════════════════════════════
   E-Commerce AI Assistant  –  main.js
   Separate page routing · SSE streaming · Typewriter effect · Particles
   ════════════════════════════════════════════════════════════════════════════ */

/* ── State ─────────────────────────────────────────────────────────────────── */
const State = {
  user: null,
  activePage: 'home',
  chat: { loading: false },
  products: {
    page: 1, perPage: 20, total: 0, totalPages: 0,
    category: '', minPrice: '', maxPrice: '', minRating: '', sortBy: 'rating',
    categories: [],
  },
  history: { page: 1, totalPages: 1 },
};

/* ── Particles ─────────────────────────────────────────────────────────────── */
function initParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  const count = window.innerWidth < 600 ? 12 : 22;
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size = Math.random() * 4 + 2;
    const colors = ['#7c6ff7','#f472b6','#34d399','#60a5fa','#a78bfa'];
    p.style.cssText = `
      width:${size}px; height:${size}px;
      left:${Math.random()*100}%;
      background:${colors[Math.floor(Math.random()*colors.length)]};
      animation-duration:${Math.random()*15+10}s;
      animation-delay:${Math.random()*12}s;
    `;
    container.appendChild(p);
  }
}

/* ── Navbar scroll effect ──────────────────────────────────────────────────── */
window.addEventListener('scroll', () => {
  document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 20);
}, { passive: true });

/* ── API Helper ────────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...opts,
    ...(opts.headers ? { headers: { 'Content-Type': 'application/json', ...opts.headers } } : {}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

/* ── Toast ──────────────────────────────────────────────────────────────────── */
function toast(msg, type = 'info', ms = 3500) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => {
    el.style.transition = '.3s'; el.style.opacity = '0'; el.style.transform = 'translateX(110%)';
    setTimeout(() => el.remove(), 350);
  }, ms);
}

/* ── Page Router ───────────────────────────────────────────────────────────── */
function navigate(page) {
  const protected_ = ['recommendations', 'history'];
  if (protected_.includes(page) && !State.user) {
    toast('Please login to access this feature.', 'warning');
    navigate('login');
    return;
  }

  // Hide all pages, show target
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

  const target = document.getElementById(`page-${page}`);
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  document.querySelectorAll(`[data-page="${page}"]`).forEach(el => el.classList.add('active'));

  State.activePage = page;

  // Close mobile menu
  const navLinks = document.getElementById('navLinks');
  const hamburger = document.getElementById('hamburger');
  navLinks.classList.remove('open');
  hamburger.classList.remove('open');

  // Lazy-load data
  if (page === 'products')         loadProducts();
  if (page === 'history')          loadHistory();
  if (page === 'home' && State.user) { /* stay on home */ }
}

function toggleMenu() {
  const nav = document.getElementById('navLinks');
  const ham = document.getElementById('hamburger');
  nav.classList.toggle('open');
  ham.classList.toggle('open');
}

/* ── Auth ────────────────────────────────────────────────────────────────────── */
async function checkAuth() {
  try {
    const data = await api('/api/auth/me');
    if (data.authenticated) { State.user = data.user; syncAuthUI(); }
  } catch (_) {}
}

function syncAuthUI() {
  const li = !!State.user;
  document.querySelectorAll('.auth-only').forEach(el => {
    el.style.display = li ? (el.tagName === 'BUTTON' || el.tagName === 'A' ? 'inline-flex' : 'flex') : 'none';
  });
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = li ? 'none' : (el.tagName === 'BUTTON' ? 'inline-flex' : 'block');
  });

  if (li) {
    const initial = State.user.name[0].toUpperCase();
    ['userAvatar', 'sidebarAvatar'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = initial;
    });
    const sn = document.getElementById('sidebarName');
    const se = document.getElementById('sidebarEmail');
    if (sn) sn.textContent = State.user.name;
    if (se) se.textContent = State.user.email;
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('loginBtn');
  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) { toast('Please fill all fields.', 'warning'); return; }

  btn.disabled = true; btn.innerHTML = '<div class="spinner spinner-sm"></div>&nbsp;Signing in…';
  try {
    const data = await api('/api/auth/login', { method:'POST', body: JSON.stringify({email,password}) });
    State.user = data.user;
    syncAuthUI();
    toast(`Welcome back, ${data.user.name}! 🎉`, 'success');
    navigate('products');
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.innerHTML = '🔑 &nbsp;Sign In';
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const btn      = document.getElementById('registerBtn');
  const name     = document.getElementById('registerName').value.trim();
  const email    = document.getElementById('registerEmail').value.trim();
  const password = document.getElementById('registerPassword').value;
  const confirm  = document.getElementById('registerConfirm').value;

  if (!name || !email || !password) { toast('Please fill all fields.', 'warning'); return; }
  if (password !== confirm)          { toast('Passwords do not match.', 'error'); return; }
  if (password.length < 6)           { toast('Password must be at least 6 characters.', 'warning'); return; }

  btn.disabled = true; btn.innerHTML = '<div class="spinner spinner-sm"></div>&nbsp;Creating…';
  try {
    const data = await api('/api/auth/register', { method:'POST', body: JSON.stringify({name,email,password}) });
    State.user = data.user;
    syncAuthUI();
    toast(`Account created! Welcome, ${data.user.name}! 🚀`, 'success');
    navigate('products');
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.innerHTML = '✨ &nbsp;Create Account';
  }
}

async function handleLogout() {
  await api('/api/auth/logout', { method: 'POST' });
  State.user = null;
  syncAuthUI();
  toast('Logged out.', 'info');
  navigate('home');
}

/* ── Products ────────────────────────────────────────────────────────────────── */
async function loadProducts(resetPage = false) {
  if (resetPage) State.products.page = 1;
  const p = State.products;
  const grid = document.getElementById('productsGrid');
  grid.innerHTML = `<div class="loading-box" style="grid-column:1/-1"><div class="spinner"></div><span>Loading products…</span></div>`;

  const params = new URLSearchParams({
    page: p.page, per_page: p.perPage,
    ...(p.category  && { category: p.category }),
    ...(p.minPrice  && { min_price: p.minPrice }),
    ...(p.maxPrice  && { max_price: p.maxPrice }),
    ...(p.minRating && { min_rating: p.minRating }),
    sort_by: p.sortBy,
  });

  try {
    const data = await api(`/api/products?${params}`);
    State.products.total      = data.total;
    State.products.totalPages = data.total_pages;
    renderCategories(data.categories);
    renderGrid(data.products);
    renderPagination();
    document.getElementById('productsCount').textContent = `${data.total.toLocaleString()} products found`;
  } catch (err) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">⚠️</div><h3>Failed to load</h3><p>${err.message}</p></div>`;
  }
}

function renderCategories(cats) {
  const list = document.getElementById('categoryList');
  list.innerHTML =
    `<div class="cat-item ${State.products.category==='' ? 'active' : ''}" onclick="setCategory('')">All Categories</div>` +
    cats.map(c => `<div class="cat-item ${State.products.category===c ? 'active' : ''}" onclick="setCategory(${JSON.stringify(c)})">${escHtml(c)}</div>`).join('');
}

function setCategory(cat) {
  State.products.category = cat;
  loadProducts(true);
}

function renderGrid(products) {
  const grid = document.getElementById('productsGrid');
  if (!products.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">🔍</div><h3>No products found</h3><p>Try adjusting your filters.</p></div>`;
    return;
  }
  grid.innerHTML = products.map(p => `
    <div class="product-card" onclick="openModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">
      ${p.discount_percentage ? `<div class="product-card__badge">${Math.round(p.discount_percentage)}% OFF</div>` : ''}
      <div class="product-card__img">
        <img src="${escHtml(p.img_link||'')}" alt="${escHtml(p.product_name)}" loading="lazy" onerror="this.style.display='none'">
      </div>
      <div class="product-card__body">
        <div class="product-card__cat">${escHtml(p.top_category)}</div>
        <div class="product-card__name">${escHtml(p.product_name)}</div>
        <div class="product-card__rating">
          <span class="stars">${stars(p.rating)}</span>
          <span>${p.rating||'N/A'}</span>
          ${p.rating_count ? `<span class="text-xs">(${Number(p.rating_count).toLocaleString()})</span>` : ''}
        </div>
        <div class="product-card__price">
          <span class="price-now">₹${p.discounted_price?.toLocaleString()||'N/A'}</span>
          ${p.actual_price ? `<span class="price-was">₹${p.actual_price.toLocaleString()}</span>` : ''}
          ${p.discount_percentage ? `<span class="price-off">${Math.round(p.discount_percentage)}% off</span>` : ''}
        </div>
      </div>
      <div class="product-card__actions">
        <a href="${escHtml(p.product_link)}" target="_blank" rel="noopener"
          class="btn btn-primary btn-sm" onclick="event.stopPropagation()">Buy Now</a>
        <button class="btn btn-ghost btn-sm"
          onclick="event.stopPropagation();chatAbout('${escAttr(p.product_name)}')">Ask AI</button>
      </div>
    </div>`).join('');
}

function renderPagination() {
  const { page, totalPages } = State.products;
  const el = document.getElementById('productsPagination');
  if (totalPages <= 1) { el.innerHTML = ''; return; }
  const range = pgRange(page, totalPages);
  let h = `<button class="page-btn" onclick="goPage(${page-1})" ${page===1?'disabled':''}>‹</button>`;
  range.forEach(n => {
    h += n === '…'
      ? `<span class="page-btn" style="cursor:default;opacity:.4">…</span>`
      : `<button class="page-btn ${n===page?'active':''}" onclick="goPage(${n})">${n}</button>`;
  });
  h += `<button class="page-btn" onclick="goPage(${page+1})" ${page===totalPages?'disabled':''}>›</button>`;
  el.innerHTML = h;
}

function pgRange(c, t) {
  if (t <= 7) return Array.from({length:t},(_,i)=>i+1);
  if (c <= 4) return [1,2,3,4,5,'…',t];
  if (c >= t-3) return [1,'…',t-4,t-3,t-2,t-1,t];
  return [1,'…',c-1,c,c+1,'…',t];
}

function goPage(p) {
  State.products.page = p;
  loadProducts();
  document.getElementById('page-products').scrollIntoView({ behavior:'smooth' });
}

function applyFilters() {
  State.products.minPrice  = document.getElementById('minPrice').value;
  State.products.maxPrice  = document.getElementById('maxPrice').value;
  const r = document.querySelector('input[name="minRating"]:checked');
  State.products.minRating = r ? r.value : '';
  loadProducts(true);
}

function resetFilters() {
  State.products = { ...State.products, category:'', minPrice:'', maxPrice:'', minRating:'', sortBy:'rating', page:1 };
  document.getElementById('minPrice').value = '';
  document.getElementById('maxPrice').value = '';
  document.querySelectorAll('input[name="minRating"]').forEach(r => r.checked = false);
  document.getElementById('sortSelect').value = 'rating';
  loadProducts();
}

/* nav search */
async function navSearch(e) {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim();
  if (!q) return;
  navigate('products');
  const grid = document.getElementById('productsGrid');
  grid.innerHTML = `<div class="loading-box" style="grid-column:1/-1"><div class="spinner"></div><span>Searching…</span></div>`;
  try {
    const data = await api(`/api/products/search?q=${encodeURIComponent(q)}&top_k=20`);
    document.getElementById('productsCount').textContent = `${data.count} results for "${q}"`;
    renderGrid(data.results);
    document.getElementById('productsPagination').innerHTML = '';
  } catch (err) { toast(err.message, 'error'); }
}

/* Product modal */
function openModal(p) {
  const html = `
    <div class="modal-bg" id="prodModal" onclick="closeModal(event)">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal__hdr">
          <span class="badge badge-primary">${escHtml(p.top_category)}</span>
          <button class="modal__close" onclick="document.getElementById('prodModal').remove()">✕</button>
        </div>
        <div class="modal__body">
          <div class="modal-prod">
            <img class="modal-prod__img" src="${escHtml(p.img_link||'')}" alt="${escHtml(p.product_name)}" onerror="this.src=''">
            <div style="flex:1;min-width:0">
              <div class="modal-prod__name">${escHtml(p.product_name)}</div>
              <div style="display:flex;align-items:center;gap:.5rem;margin:.6rem 0">
                <span class="stars">${stars(p.rating)}</span>
                <span class="text-sm text-muted">${p.rating||'N/A'}/5
                  ${p.rating_count ? `(${Number(p.rating_count).toLocaleString()} ratings)` : ''}</span>
              </div>
              <div class="product-card__price" style="margin:.5rem 0">
                <span class="price-now" style="font-size:1.4rem">₹${p.discounted_price?.toLocaleString()||'N/A'}</span>
                ${p.actual_price ? `<span class="price-was">₹${p.actual_price.toLocaleString()}</span>` : ''}
                ${p.discount_percentage ? `<span class="price-off">${Math.round(p.discount_percentage)}% off</span>` : ''}
              </div>
              <div class="modal-prod__desc">${escHtml(p.about_product)}</div>
              <div style="display:flex;gap:.75rem;margin-top:1.25rem;flex-wrap:wrap">
                <a href="${escHtml(p.product_link)}" target="_blank" rel="noopener" class="btn btn-primary">
                  🛒 Buy on Amazon
                </a>
                <button class="btn btn-ghost" onclick="document.getElementById('prodModal').remove();chatAbout('${escAttr(p.product_name)}')">
                  🤖 Ask AI
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
}
function closeModal(e) { if (e.target.id==='prodModal') e.target.remove(); }

/* ── AI CHAT with SSE STREAMING ─────────────────────────────────────────────── */
function chatAbout(name) {
  navigate('recommendations');
  const ta = document.getElementById('chatInput');
  ta.value = `Tell me about "${name}" — is it worth buying?`;
  ta.focus();
}

function useSuggestion(text) {
  document.getElementById('chatInput').value = text;
  document.getElementById('chatInput').focus();
}

function addUserMsg(text) {
  const msgs = document.getElementById('chatMessages');
  const initial = State.user ? State.user.name[0].toUpperCase() : 'U';
  msgs.insertAdjacentHTML('beforeend', `
    <div class="chat-msg user">
      <div class="msg-av user-av">${initial}</div>
      <div class="chat-bubble">${escHtml(text)}</div>
    </div>`);
  msgs.scrollTop = msgs.scrollHeight;
}

function showTypingIndicator() {
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="chat-msg assistant" id="typingMsg">
      <div class="msg-av">🤖</div>
      <div class="chat-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>
    </div>`);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTyping() {
  document.getElementById('typingMsg')?.remove();
}

/* Creates the assistant bubble that we'll stream text INTO */
function createStreamBubble() {
  removeTyping();
  const msgs = document.getElementById('chatMessages');
  const id = `stream-${Date.now()}`;
  msgs.insertAdjacentHTML('beforeend', `
    <div class="chat-msg assistant" id="${id}">
      <div class="msg-av">🤖</div>
      <div class="chat-bubble">
        <div class="ai-text" id="${id}-text"></div>
        <span class="stream-cursor" id="${id}-cursor"></span>
      </div>
    </div>`);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

/* Append a chunk of text — convert markdown inline as it arrives */
function appendChunk(bubbleId, chunk) {
  const textEl = document.getElementById(`${bubbleId}-text`);
  if (!textEl) return;
  // Accumulate raw text, re-render markdown each time
  textEl._raw = (textEl._raw || '') + chunk;
  textEl.innerHTML = mdToHtml(textEl._raw);
  const msgs = document.getElementById('chatMessages');
  msgs.scrollTop = msgs.scrollHeight;
}

function finishStream(bubbleId, products) {
  // Remove cursor
  document.getElementById(`${bubbleId}-cursor`)?.remove();

  // Append product cards after the text
  if (products && products.length) {
    const bubble = document.getElementById(bubbleId)?.querySelector('.chat-bubble');
    if (bubble) {
      const div = document.createElement('div');
      div.className = 'rec-products';
      div.innerHTML = products.map((p, i) => `
        <div class="rec-card" style="animation-delay:${i*0.08}s">
          <img class="rec-card__img" src="${escHtml(p.img_link||'')}" alt="${escHtml(p.product_name)}"
            onerror="this.style.display='none'" loading="lazy">
          <div class="rec-card__info">
            <div class="rec-card__name">${escHtml(p.product_name)}</div>
            <div class="rec-card__rating">${stars(p.rating)} ${p.rating||''}</div>
            <div class="rec-card__price">₹${p.discounted_price?.toLocaleString()||'N/A'}</div>
            <div style="display:flex;gap:.4rem;margin-top:.4rem">
              <a href="${escHtml(p.product_link)}" target="_blank" rel="noopener" class="btn btn-success btn-sm">Buy</a>
              <button class="btn btn-ghost btn-sm" onclick="openModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">View</button>
            </div>
          </div>
        </div>`).join('');
      bubble.appendChild(div);
    }
  }

  const msgs = document.getElementById('chatMessages');
  msgs.scrollTop = msgs.scrollHeight;
}

async function sendRecommendation() {
  if (!State.user) { toast('Please login to use AI chat.', 'warning'); navigate('login'); return; }
  if (State.chat.loading) return;

  const ta    = document.getElementById('chatInput');
  const query = ta.value.trim();
  if (!query) return;

  ta.value = ''; ta.style.height = 'auto';
  State.chat.loading = true;
  document.getElementById('sendBtn').disabled = true;

  addUserMsg(query);
  showTypingIndicator();

  let products = [];
  let bubbleId = null;

  try {
    const response = await fetch('/api/recommend/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Request failed');
    }

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // keep incomplete part

      for (const part of parts) {
        const lines  = part.split('\n');
        const event  = lines.find(l => l.startsWith('event:'))?.replace('event:', '').trim();
        const dataLine = lines.find(l => l.startsWith('data:'))?.replace('data:', '').trim();
        if (!dataLine) continue;

        const payload = JSON.parse(dataLine);

        if (event === 'products') {
          // Products arrived — show typing a bit longer, then create stream bubble
          products = payload;
          removeTyping();
          bubbleId = createStreamBubble();
        }

        if (event === 'chunk' && bubbleId) {
          appendChunk(bubbleId, payload.chunk);
        }

        if (event === 'error') {
          throw new Error(payload.error || 'Streaming error');
        }

        if (event === 'done') {
          finishStream(bubbleId, products);
        }
      }
    }

  } catch (err) {
    removeTyping();
    if (!bubbleId) bubbleId = createStreamBubble();
    appendChunk(bubbleId, `⚠️ ${err.message}`);
    document.getElementById(`${bubbleId}-cursor`)?.remove();
  } finally {
    State.chat.loading = false;
    document.getElementById('sendBtn').disabled = false;
  }
}

/* ── Chat History ────────────────────────────────────────────────────────────── */
async function loadHistory(resetPage = false) {
  if (resetPage) State.history.page = 1;
  const container = document.getElementById('historyList');
  container.innerHTML = `<div class="loading-box"><div class="spinner"></div><span>Loading…</span></div>`;

  try {
    const data = await api(`/api/history?page=${State.history.page}&per_page=10`);
    State.history.totalPages = data.total_pages;
    renderHistory(data.history, data.total);
    renderHistPagination();
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><h3>Failed to load</h3><p>${err.message}</p></div>`;
  }
}

function renderHistory(items, total) {
  const container = document.getElementById('historyList');
  document.getElementById('historyCount').textContent = `${total} conversation${total!==1?'s':''}`;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state"><div class="icon">💬</div><h3>No history yet</h3>
      <p>Start chatting with the AI recommender.</p>
      <button class="btn btn-primary mt-2" onclick="navigate('recommendations')">Start Chat</button></div>`;
    return;
  }
  container.innerHTML = `<div class="hist-grid">` + items.map(item => `
    <div class="hist-item" id="hist-${item.id}">
      <div class="hist-item__top" onclick="toggleHist(${item.id})">
        <div>
          <div class="hist-query">💬 ${escHtml(item.query)}</div>
          <div style="display:flex;gap:.5rem;margin-top:.35rem;flex-wrap:wrap;align-items:center">
            <span class="badge badge-primary">${item.products?.length||0} products</span>
            <span class="hist-meta">🕒 ${fmtDate(item.timestamp)}</span>
          </div>
        </div>
        <div style="display:flex;gap:.5rem;align-items:center;flex-shrink:0">
          <span style="color:var(--text-muted);font-size:.8rem" id="hist-arrow-${item.id}">▼</span>
          <button class="btn btn-danger btn-sm" style="padding:.3rem .6rem"
            onclick="event.stopPropagation();deleteHist(${item.id})">🗑</button>
        </div>
      </div>
      <div class="hist-body hidden" id="hist-body-${item.id}">
        <div class="hist-ai ai-text">${mdToHtml(item.ai_response)}</div>
        ${item.products?.length ? `
          <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin-bottom:.5rem">
            🛒 Retrieved Products
          </div>
          <div class="hist-prods">
            ${item.products.map(p => `
              <div class="hist-prod">
                <img src="${escHtml(p.img_link||'')}" alt="${escHtml(p.product_name)}" onerror="this.style.display='none'" loading="lazy">
                <div class="hist-prod__info">
                  <div class="hist-prod__name">${escHtml(p.product_name)}</div>
                  <div class="hist-prod__price">₹${p.discounted_price?.toLocaleString()||'N/A'}</div>
                  <a href="${escHtml(p.product_link)}" target="_blank" rel="noopener"
                    class="btn btn-primary btn-sm w-full mt-1" style="font-size:.68rem">Buy</a>
                </div>
              </div>`).join('')}
          </div>` : ''}
      </div>
    </div>`).join('') + '</div>';
}

function toggleHist(id) {
  const body  = document.getElementById(`hist-body-${id}`);
  const arrow = document.getElementById(`hist-arrow-${id}`);
  const open  = !body.classList.contains('hidden');
  body.classList.toggle('hidden', open);
  if (arrow) arrow.textContent = open ? '▼' : '▲';
}

async function deleteHist(id) {
  if (!confirm('Delete this conversation?')) return;
  try {
    await api(`/api/history/${id}`, { method:'DELETE' });
    document.getElementById(`hist-${id}`)?.remove();
    toast('Deleted.', 'success');
  } catch (err) { toast(err.message, 'error'); }
}

async function clearAllHistory() {
  if (!confirm('Clear ALL history? This cannot be undone.')) return;
  try {
    await api('/api/history/clear', { method:'DELETE' });
    loadHistory(true);
    toast('History cleared.', 'success');
  } catch (err) { toast(err.message, 'error'); }
}

function renderHistPagination() {
  const { page, totalPages } = State.history;
  const el = document.getElementById('historyPagination');
  if (totalPages <= 1) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <button class="btn btn-outline btn-sm" onclick="histPage(${page-1})" ${page===1?'disabled':''}>‹ Prev</button>
    <span class="text-sm text-muted">Page ${page} / ${totalPages}</span>
    <button class="btn btn-outline btn-sm" onclick="histPage(${page+1})" ${page===totalPages?'disabled':''}>Next ›</button>`;
}

function histPage(p) { State.history.page = p; loadHistory(); }

/* ── Helpers ─────────────────────────────────────────────────────────────────── */
function stars(r) {
  const v = parseFloat(r)||0;
  return '★'.repeat(Math.floor(v)) + (v%1>=.5?'½':'') + '☆'.repeat(5-Math.floor(v)-(v%1>=.5?1:0));
}
function escHtml(s) { const d=document.createElement('div'); d.textContent=String(s||''); return d.innerHTML; }
function escAttr(s) { return String(s||'').replace(/'/g,"\\'").replace(/"/g,'&quot;'); }
function fmtDate(iso) {
  return new Date(iso).toLocaleString('en-IN',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
}

/* Minimal markdown → HTML */
function mdToHtml(t) {
  if (!t) return '';
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/^\* (.+)$/gm,'<li>$1</li>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>)/g,'<ul>$1</ul>')
    .replace(/\n\n/g,'</p><p>')
    .replace(/\n/g,'<br>');
}

/* ── Init ────────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  initParticles();

  await checkAuth();
  syncAuthUI();

  // Default page
  navigate(State.user ? 'products' : 'home');

  // Login / Register
  document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
  document.getElementById('registerForm')?.addEventListener('submit', handleRegister);

  // Sort select
  document.getElementById('sortSelect')?.addEventListener('change', e => {
    State.products.sortBy = e.target.value;
    loadProducts(true);
  });

  // Nav search
  document.getElementById('navSearchInput')?.addEventListener('keydown', navSearch);

  // Chat textarea auto-resize + Enter send
  const ta = document.getElementById('chatInput');
  if (ta) {
    ta.addEventListener('input', () => {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    });
    ta.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendRecommendation(); }
    });
  }
});
