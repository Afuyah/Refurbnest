document.addEventListener('DOMContentLoaded', () => {
  // ——————— DOM Caching ———————
  const sidebar       = document.getElementById('cartSidebar');
  const overlay       = document.getElementById('cartOverlay');
  const icon          = document.getElementById('cartIcon');
  const badge         = document.getElementById('cartBadge');
  const closeBtn      = document.getElementById('closeCartBtn');
  const itemsContainer= document.getElementById('cartItems');
  const subtotalEl    = document.getElementById('cartSubtotal');
  const toastContainer= document.getElementById('toastContainer');
  const csrfToken     = document.querySelector('meta[name="csrf-token"]').content;

  // ——————— State ———————
  let cart = { items: [], total: 0, count: 0 };

  // ——————— Helpers ———————
  const showToast = (msg, type = 'success') => {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i>
        <span>${msg}</span>
      </div>`;
    toastContainer.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => toast.classList.remove('show'), 3000);
    toast.addEventListener('transitionend', () => toast.remove());
  };

  const updateUI = () => {
    // Badge
    badge.textContent = cart.count;
    badge.style.display = cart.count ? 'block' : 'none';
    // Subtotal
    subtotalEl.textContent = `$${cart.total.toFixed(2)}`;

    // Items
    itemsContainer.innerHTML = '';
    if (!cart.items.length) {
      itemsContainer.innerHTML = `
        <div class="empty-cart">
          <i class="fas fa-shopping-cart"></i>
          <p>Your cart is empty</p>
        </div>`;
      return;
    }

    const frag = document.createDocumentFragment();
    cart.items.forEach(({ id, name, price, current_price, quantity, available }) => {
      const itemEl = document.createElement('div');
      itemEl.className = 'cart-item';
      itemEl.innerHTML = `
        <div class="item-info">
          <h4>${name}</h4>
          <div class="item-meta">
            <span class="quantity">${quantity} × $${price.toFixed(2)}</span>
            ${current_price < price ? `<span class="price-warning">Now $${current_price.toFixed(2)}</span>` : ''}
            ${!available ? '<span class="stock-warning">(Out of stock)</span>' : ''}
          </div>
        </div>
        <button class="remove-item" data-id="${id}">
          <i class="fas fa-trash"></i>
        </button>`;
      frag.appendChild(itemEl);
    });
    itemsContainer.appendChild(frag);
  };

  const fetchCart = async () => {
    try {
      const res = await fetch('/cart/json');
      if (!res.ok) throw new Error('Failed to load cart');
      const data = await res.json();
      cart = { items: data.items, total: data.total, count: data.count };
      updateUI();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const modifyCart = async (url, method, payload = {}) => {
    try {
      const res = await fetch(url, {
        method,
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
      showToast(err.message, 'error');
      throw err;
    }
  };

  // ——————— Event Handlers ———————
  const onAddToCart = async (e) => {
    const btn = e.target.closest('.add-to-cart-btn');
    if (!btn) return;
    btn.disabled = true;
    const id = btn.dataset.productId;
    if (!id) {
      showToast('Product ID missing', 'error');
      btn.disabled = false;
      return;
    }
    try {
      const { message } = await modifyCart(`/cart/add/${id}`, 'POST');
      showToast(message || 'Item added to cart');
    } finally {
      btn.disabled = false;
    }
  };

  const onRemoveItem = async (e) => {
    const btn = e.target.closest('.remove-item');
    if (!btn) return;
    btn.disabled = true;
    const id = btn.dataset.id;
    try {
      await modifyCart(`/cart/remove/${id}`, 'DELETE');
      showToast('Item removed from cart');
    } finally {
      btn.disabled = false;
    }
  };

  // ——————— Visibility Controls ———————
  const openCart  = () => { fetchCart(); sidebar.classList.add('open'); overlay.classList.add('show'); };
  const closeCart = () => { sidebar.classList.remove('open'); overlay.classList.remove('show'); };

  // ——————— Listeners ———————
  icon.addEventListener('click', openCart);
  closeBtn.addEventListener('click', closeCart);
  overlay.addEventListener('click', closeCart);
  document.body.addEventListener('click', onAddToCart);
  itemsContainer.addEventListener('click', onRemoveItem);

  // ——————— Init ———————
  fetchCart();
});


document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('checkoutBtn');
  console.log('checkoutBtn element is', btn);
  if (!btn) return;

  btn.addEventListener('click', async () => {
    console.log('checkoutBtn clicked!!');

    try {
      console.log('Fetching /cart/summary…');
      const response = await fetch('/cart/summary', {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('Fetch completed:', response.status);

      if (!response.ok) {
        console.error('Non-OK status:', response.status);
        showToast('Could not fetch cart summary', 'error');
        return;
      }

      const data = await response.json();
      console.log('Cart summary data:', data);

      if (data.count === 0) {
        showToast('Your cart is empty.', 'warning');
        return;
      }

      console.log('Redirecting to /cart/checkout');
      // 🔑 Use the blueprint’s prefix
      window.location.href = '/cart/checkout';

    } catch (err) {
      console.error('Error during checkout:', err);
      showToast('There was a problem starting checkout.', 'error');
    }
  });
});
