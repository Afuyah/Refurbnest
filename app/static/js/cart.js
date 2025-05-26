document.addEventListener('DOMContentLoaded', () => {
  // ——————— DOM Caching ———————
  const sidebar        = document.getElementById('cartSidebar');
  const overlay        = document.getElementById('cartOverlay');
  const icon           = document.getElementById('cartIcon');
  const badge          = document.getElementById('cartBadge');
  const closeBtn       = document.getElementById('closeCartBtn');
  const itemsContainer = document.getElementById('cartItems');
  const subtotalEl     = document.getElementById('cartSubtotal');
  const toastContainer = document.getElementById('toastContainer');
  const csrfToken      = document.querySelector('meta[name="csrf-token"]').content;

  // ——————— State ———————
  let cart = { items: [], total: 0, count: 0 };

  // ——————— Helpers ———————
  // Bootstrap-based toast helper
  const showToast = (message, type = 'success') => {
    const toastEl = document.createElement('div');
    toastEl.innerHTML = `
      <div class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>`;
    const toastNode = toastEl.firstElementChild;
    toastContainer.appendChild(toastNode);
    const bsToast = new bootstrap.Toast(toastNode, { delay: 3000 });
    bsToast.show();
    toastNode.addEventListener('hidden.bs.toast', () => toastNode.remove());
  };

  // Error banner at top of sidebar
  const showErrorBanner = msg => {
    const banner = document.createElement('div');
    banner.className = 'alert alert-danger text-center mb-0';
    banner.textContent = msg;
    sidebar.prepend(banner);
  };

  // Loading spinner state
  const setLoading = isLoading => {
    closeBtn.disabled = isLoading;
    if (isLoading) {
      itemsContainer.innerHTML = `
        <div class="text-center py-5">
          <div class="spinner-border" role="status"><span class="visually-hidden">Loading…</span></div>
        </div>`;
    }
  };

  // Update UI from cart state
  const updateUI = () => {
    // Badge
    badge.textContent = cart.count;
    badge.style.display = cart.count ? 'inline-flex' : 'none';
    // Subtotal
    subtotalEl.textContent = `$${cart.total.toFixed(2)}`;

    // Items
    if (!cart.items.length) {
      itemsContainer.innerHTML = `
        <div class="empty-cart text-center py-5">
          <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
          <h6 class="text-muted">Your cart is empty</h6>
          <p class="small text-muted">Start shopping to add items</p>
        </div>`;
      return;
    }

    const frag = document.createDocumentFragment();
    cart.items.forEach(item => {
      const { id, name, price, current_price, quantity, available } = item;
      const div = document.createElement('div');
      div.className = 'cart-item d-flex justify-content-between align-items-center py-2 border-bottom';
      div.innerHTML = `
        <div>
          <h6 class="mb-1">${name}</h6>
          <small class="text-muted">
            ${quantity} × $${price.toFixed(2)}
            ${current_price < price ? `<span class="text-danger ms-2">Now $${current_price.toFixed(2)}</span>` : ''}
            ${!available ? '<span class="text-warning ms-2">(Out of stock)</span>' : ''}
          </small>
        </div>
        <button class="btn btn-sm btn-outline-danger remove-item" data-id="${id}" aria-label="Remove ${name}">
          <i class="fas fa-trash-alt"></i>
        </button>`;
      frag.appendChild(div);
    });
    itemsContainer.innerHTML = '';
    itemsContainer.appendChild(frag);
  };

  // Fetch cart JSON
  const fetchCart = async () => {
    setLoading(true);
    try {
      const res = await fetch('/cart/json', {
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken }
      });
      if (!res.ok) throw new Error('Failed to load cart');
      const data = await res.json();
      cart = { items: data.items, total: data.total, count: data.count };
      updateUI();
    } catch (err) {
      showErrorBanner(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Add / remove / clear operations
  const modifyCart = async (url, method, payload = {}) => {
    setLoading(true);
    try {
      const res = await fetch(url, {
        method,
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: Object.keys(payload).length ? JSON.stringify(payload) : null
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Cart operation failed');
      }
      const data = await res.json();
      cart = { items: data.items, total: data.total, count: data.count };
      updateUI();
      return data;
    } catch (err) {
      showToast(err.message, 'danger');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // ——————— Event Handlers ———————
  const onAddToCart = async e => {
    const btn = e.target.closest('.add-to-cart-btn');
    if (!btn) return;
    btn.disabled = true;
    try {
      const id = btn.dataset.productId;
      if (!id) throw new Error('Product ID missing');
      const { message } = await modifyCart(`/cart/add/${id}`, 'POST');
      showToast(message || 'Added to cart', 'success');
    } catch (err) {
      console.error(err);
    } finally {
      btn.disabled = false;
    }
  };

  const onRemoveItem = async e => {
  const btn = e.target.closest('.remove-item');
  if (!btn) return;
  btn.disabled = true;
  try {
    await modifyCart(`/cart/remove/${btn.dataset.id}`, 'DELETE');
    showToast('Removed from cart', 'warning');
    await fetchCart();    // ← Force re-load and re-render of remaining items
  } catch (err) {
    console.error(err);
  } finally {
    btn.disabled = false;
  }
};


  const onCheckout = async () => {
  try {
    const res = await fetch('/cart/summary', {
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!res.ok) throw new Error('Could not fetch summary');
    const data = await res.json();

    if (data.count === 0) {
      showToast('Your cart is empty.', 'info');
      return;
    }

    // ✅ Correct route to initiate checkout
    window.location.href = '/cart/checkout/start';
    
  } catch (err) {
    showToast(err.message, 'danger');
  }
};


  // ——————— Focus Trap ———————
  const trapFocus = () => {
    const focusable = sidebar.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusable[0], last = focusable[focusable.length - 1];
    first.focus();
    sidebar.addEventListener('keydown', e => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    });
  };

  // ——————— Open / Close ———————
  const openCart  = () => { fetchCart(); sidebar.classList.add('open'); overlay.classList.add('active'); trapFocus(); };
  const closeCart = () => { sidebar.classList.remove('open'); overlay.classList.remove('active'); icon.focus(); };

  // ——————— Listeners ———————
  icon.addEventListener('click', openCart);
  closeBtn.addEventListener('click', closeCart);
  overlay.addEventListener('click', closeCart);
  document.body.addEventListener('click', onAddToCart);
  itemsContainer.addEventListener('click', onRemoveItem);
  document.getElementById('checkoutBtn')?.addEventListener('click', onCheckout);

  // ——————— Init ———————
  fetchCart();
});