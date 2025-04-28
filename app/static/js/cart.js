document.addEventListener('DOMContentLoaded', () => {
  // Cart UI Elements
  const cartElements = {
      sidebar: document.getElementById('cartSidebar'),
      overlay: document.getElementById('cartOverlay'),
      icon: document.getElementById('cartIcon'),
      badge: document.getElementById('cartBadge'),
      closeBtn: document.getElementById('closeCartBtn'),
      itemsContainer: document.getElementById('cartItems'),
      subtotalEl: document.getElementById('cartSubtotal'),
      toastContainer: document.getElementById('toastContainer')
  };

  // Cart State Management
  let cartState = {
      items: [],
      total: 0,
      count: 0,
      uniqueItems: 0
  };

  // Cart Visibility Controls
  const cartVisibility = {
      open: () => {
          fetchCartData();
          cartElements.sidebar.classList.add('open');
          cartElements.overlay.classList.add('show');
      },
      close: () => {
          cartElements.sidebar.classList.remove('open');
          cartElements.overlay.classList.remove('show');
      }
  };

  // Event Listeners
  cartElements.icon.addEventListener('click', cartVisibility.open);
  cartElements.closeBtn.addEventListener('click', cartVisibility.close);
  cartElements.overlay.addEventListener('click', cartVisibility.close);

  // Cart Actions
  document.body.addEventListener('click', async (e) => {
      const btn = e.target.closest('.add-to-cart-btn');
      if (!btn) return;

      const productId = btn.dataset.productId;
      if (!productId) return showToast('Product ID missing', 'error');

      try {
          const response = fetch(`/cart/add-to-cart/${productId}`, { 
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
          })
          
          if (!response.ok) {
              const error = await response.json();
              throw new Error(error.message || 'Add to cart failed');
          }

          const data = await response.json();
          updateCartState(data);
          showToast(data.message || 'Item added to cart 🛒');
      } catch (error) {
          showToast(error.message, 'error');
      }
  });

  // Cart Data Management
  async function fetchCartData() {
      try {
          const response = await fetch('/cart/cart/json');
          if (!response.ok) throw new Error('Failed to load cart');
          
          const data = await response.json();
          updateCartState(data);
      } catch (error) {
          showToast(error.message, 'error');
      }
  }

  function updateCartState(data) {
      cartState = {
          items: data.items || [],
          total: data.total || 0,
          count: data.count || 0,
          uniqueItems: data.unique_items || 0
      };

      renderCartItems();
      updateBadge();
      updateSubtotal();
  }

  // Cart Rendering
  function renderCartItems() {
      cartElements.itemsContainer.innerHTML = '';
      
      if (cartState.items.length === 0) {
          cartElements.itemsContainer.innerHTML = `
              <div class="empty-cart">
                  <i class="fas fa-shopping-cart"></i>
                  <p>Your cart is empty</p>
              </div>
          `;
          return;
      }

      const fragment = document.createDocumentFragment();
      
      cartState.items.forEach(item => {
          const itemEl = document.createElement('div');
          itemEl.className = 'cart-item';
          itemEl.innerHTML = `
              <div class="item-info">
                  <h4>${item.name}</h4>
                  <div class="item-meta">
                      <span class="quantity">${item.quantity} × $${item.price.toFixed(2)}</span>
                      ${item.current_price !== item.price ? 
                          `<span class="price-warning">Now $${item.current_price.toFixed(2)}</span>` : ''}
                      ${!item.available ? '<span class="stock-warning">(Out of stock)</span>' : ''}
                  </div>
              </div>
              <button class="remove-item" data-id="${item.id}">
                  <i class="fas fa-trash"></i>
              </button>
          `;

          itemEl.querySelector('.remove-item').addEventListener('click', handleItemRemoval);
          fragment.appendChild(itemEl);
      });

      cartElements.itemsContainer.appendChild(fragment);
  }

  // Item Removal Handler
async function handleItemRemoval(e) {
  const itemId = e.currentTarget.dataset.id;
  try {
      const response = await fetch(`/cart/remove/${itemId}`, { 
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
          }
      });

      if (!response.ok) {
          const error = await response.json();
          throw new Error(error.message || 'Failed to remove item');
      }

      const data = await response.json();
      updateCartState(data);
      updateBadge();
      updateSubtotal();
      showToast('Item removed from cart');
  } catch (error) {
      showToast(error.message, 'error');
  }
}

// UI Updates
function updateBadge() {
  const count = cartState.count || 0;
  cartElements.badge.textContent = count;
  cartElements.badge.style.display = count > 0 ? 'block' : 'none';
}

function updateSubtotal() {
  const total = cartState.total ? cartState.total.toFixed(2) : '0.00';
  cartElements.subtotalEl.textContent = `$${total}`;
}



  // Toast System
  function showToast(message, type = 'success') {
      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.innerHTML = `
          <div class="toast-content">
              <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i>
              <span>${message}</span>
          </div>
      `;
      
      cartElements.toastContainer.appendChild(toast);
      
      setTimeout(() => {
          toast.classList.add('show');
          setTimeout(() => {
              toast.classList.remove('show');
              setTimeout(() => toast.remove(), 300);
          }, 3000);
      }, 10);
  }

  
  // Initial Load
  fetchCartData();
});