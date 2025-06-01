document.addEventListener('DOMContentLoaded', () => {
  // ——————— DOM Elements ———————
  const sidebar = document.getElementById('cartSidebar');
  const overlay = document.getElementById('cartOverlay');
  const icon = document.getElementById('cartIcon');
  const badge = document.getElementById('cartBadge');
  const closeBtn = document.getElementById('closeCartBtn');
  const itemsContainer = document.getElementById('cartItems');
  const subtotalEl = document.getElementById('cartSubtotal');
  const checkoutBtn = document.getElementById('checkoutBtn');
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

  // ——————— State ———————
  let cart = { items: [], total: 0, count: 0 };
  let isSidebarOpen = false;

  // ——————— Premium Toast Notifications ———————
  const showToast = (message, type = 'success', duration = 4000) => {
    const toastId = `toast-${Date.now()}`;
    const iconMap = {
      success: 'fa-circle-check',
      error: 'fa-circle-xmark',
      warning: 'fa-triangle-exclamation',
      info: 'fa-circle-info'
    };
    
    const colorMap = {
      success: 'bg-emerald-500',
      error: 'bg-red-500',
      warning: 'bg-amber-400',
      info: 'bg-blue-400'
    };

    const toastEl = document.createElement('div');
    toastEl.id = toastId;
    toastEl.className = `
      fixed top-4 right-4 z-[9999] w-full max-w-xs
      transform transition-all duration-300
      translate-x-[120%] opacity-0
      rounded-xl shadow-xl overflow-hidden
      ${colorMap[type] || 'bg-indigo-500'}
      ${type === 'warning' ? 'text-amber-900' : 'text-white'}
    `;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
      <div class="flex items-start p-4">
        <div class="flex-shrink-0 pt-0.5">
          <i class="fas ${iconMap[type] || 'fa-bell'} text-xl"></i>
        </div>
        <div class="ml-3 flex-1">
          <p class="text-sm font-medium">${message}</p>
        </div>
        <button type="button" class="ml-4 flex-shrink-0 rounded-lg p-1
          ${type === 'warning' ? 'hover:bg-amber-500' : 'hover:bg-white/10'}
          focus:outline-none focus:ring-2 focus:ring-white/50"
          onclick="document.getElementById('${toastId}').remove()">
          <span class="sr-only">Close</span>
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="h-1 w-full bg-black/10">
        <div class="h-full ${colorMap[type] || 'bg-indigo-500'} animate-progress"></div>
      </div>
    `;

    document.body.appendChild(toastEl);
    
    // Show animation
    setTimeout(() => {
      toastEl.classList.remove('translate-x-[120%]', 'opacity-0');
      toastEl.classList.add('translate-x-0', 'opacity-100');
    }, 10);

    // Auto-dismiss
    const autoDismiss = setTimeout(() => {
      dismissToast(toastId);
    }, duration);

    // Pause on hover
    toastEl.addEventListener('mouseenter', () => {
      clearTimeout(autoDismiss);
      toastEl.querySelector('.animate-progress').style.animationPlayState = 'paused';
    });

    toastEl.addEventListener('mouseleave', () => {
      const newDismiss = setTimeout(() => {
        dismissToast(toastId);
      }, duration);
      
      toastEl.querySelector('.animate-progress').style.animationPlayState = 'running';
      toastEl.dataset.dismissTimeout = newDismiss;
    });
  };

  function dismissToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
      toast.classList.add('translate-x-[120%]', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }
  }

  // ——————— Cart Operations ———————
  const setLoading = (isLoading) => {
    closeBtn.disabled = isLoading;
    if (isLoading) {
      itemsContainer.innerHTML = `
        <div class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>`;
      if (checkoutBtn) checkoutBtn.disabled = true;
    } else {
      if (checkoutBtn) checkoutBtn.disabled = cart.count === 0;
    }
  };

  const updateUI = () => {
    // Update badge
    badge.textContent = cart.count;
    badge.style.display = cart.count ? 'inline-flex' : 'none';
    
    // Update subtotal
    subtotalEl.textContent = `$${cart.total.toFixed(2)}`;

    // Empty state
    if (!cart.items.length) {
      itemsContainer.innerHTML = `
        <div class="empty-cart text-center py-5">
          <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
          <h6 class="text-muted">Your cart is empty</h6>
          <button class="btn btn-outline-primary mt-3" onclick="closeCart()">
            Continue Shopping
          </button>
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

   const fetchCart = async () => {
    setLoading(true);
    try {
      const res = await fetch('/cart/json', {
        headers: { 'X-CSRFToken': csrfToken }
      });
      if (!res.ok) throw new Error('Failed to load cart');
      
      const data = await res.json();
      cart = { 
        items: data.items || [], 
        total: data.total || 0, 
        count: data.count || 0 
      };
      updateUI();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

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
      showToast(err.message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // ——————— Event Handlers ———————
  const onAddToCart = async (e) => {
    const btn = e.target.closest('.add-to-cart-btn');
    if (!btn) return;
    
    const originalText = btn.innerHTML;
    btn.innerHTML = `
      <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
      Adding...
    `;
    btn.disabled = true;
    
    try {
      const id = btn.dataset.productId;
      if (!id) throw new Error('Product ID missing');
      
      const { message } = await modifyCart(`/cart/add/${id}`, 'POST');
      showToast(message || 'Added to cart', 'success');
      
      // If sidebar is open, refresh the cart view
      if (isSidebarOpen) {
        await fetchCart();
      }
    } catch (err) {
      console.error(err);
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  };

  const onRemoveItem = async (e) => {
    const btn = e.target.closest('.remove-item');
    if (!btn) return;
    
    btn.disabled = true;
    try {
      // Remove item from server
      const res = await fetch(`/cart/remove/${btn.dataset.id}`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': csrfToken }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Failed to remove item');
      }
      
      // Force complete refresh of cart data
      await fetchCart();
      
      showToast('Item removed from cart', 'warning');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  };

  const onCheckout = async () => {
    if (cart.count === 0) {
      showToast('Your cart is empty', 'info');
      return;
    }
    
    checkoutBtn.disabled = true;
    checkoutBtn.innerHTML = `
      <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
      Processing...
    `;
    
    try {
      // Check for out of stock items
      const outOfStockItems = cart.items.filter(item => !item.available);
      if (outOfStockItems.length > 0) {
        throw new Error('Some items in your cart are out of stock. Please remove them before checkout.');
      }
      
      // Proceed to checkout
      window.location.href = '/cart/checkout/start';
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      checkoutBtn.disabled = false;
      checkoutBtn.innerHTML = 'Proceed to Checkout';
    }
  };

  // ——————— Sidebar Management ———————
  const trapFocus = () => {
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusable = sidebar.querySelectorAll(focusableElements);
    const firstElement = focusable[0];
    const lastElement = focusable[focusable.length - 1];

    firstElement.focus();

    sidebar.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    });
  };

  const openCart = async () => {
    if (isSidebarOpen) return;
    
    document.body.style.overflow = 'hidden';
    sidebar.classList.add('open');
    overlay.classList.add('active');
    isSidebarOpen = true;
    
    // Set aria attributes
    sidebar.setAttribute('aria-hidden', 'false');
    overlay.setAttribute('aria-hidden', 'false');
    
    try {
      await fetchCart();
      trapFocus();
    } catch (err) {
      console.error(err);
    }
  };

  const closeCart = () => {
    if (!isSidebarOpen) return;
    
    document.body.style.overflow = '';
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    isSidebarOpen = false;
    
    // Set aria attributes
    sidebar.setAttribute('aria-hidden', 'true');
    overlay.setAttribute('aria-hidden', 'true');
    
    // Return focus to cart icon
    icon.focus();
  };

  // ——————— Event Listeners ———————
  icon.addEventListener('click', openCart);
  closeBtn.addEventListener('click', closeCart);
  overlay.addEventListener('click', closeCart);
  document.body.addEventListener('click', onAddToCart);
  itemsContainer.addEventListener('click', onRemoveItem);
  if (checkoutBtn) checkoutBtn.addEventListener('click', onCheckout);

  // Close cart when pressing Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isSidebarOpen) {
      closeCart();
    }
  });

  // ——————— Initialize ———————
  fetchCart();

  // Add CSS animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes progress {
      from { transform: scaleX(1); }
      to { transform: scaleX(0); }
    }
    .animate-progress {
      animation: progress linear forwards;
      transform-origin: left;
    }
    .pulse {
      animation: pulse 0.5s ease-in-out;
    }
    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.1); }
      100% { transform: scale(1); }
    }
    #cartSidebar {
      transform: translateX(100%);
      transition: transform 0.3s ease;
    }
    #cartSidebar.open {
      transform: translateX(0);
    }
    #cartOverlay {
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0.3s ease;
    }
    #cartOverlay.active {
      opacity: 1;
      visibility: visible;
    }
  `;
  document.head.appendChild(style);
});