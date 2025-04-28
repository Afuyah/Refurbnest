document.addEventListener('DOMContentLoaded', () => {
    const orderSummary = document.getElementById('order-summary');
    const orderTotal   = document.getElementById('order-total');
    const form         = document.getElementById('checkout-form');
  
    // 1. Populate Order Summary only if element exists
    if (orderSummary && orderTotal) {
      (async function loadOrderSummary() {
        try {
          const res = await fetch('/cart/summary', {
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' }
          });
          if (!res.ok) throw new Error('Failed to load cart summary');
  
          const data = await res.json();
          // convert items object to array if needed
          const items = Array.isArray(data.items)
            ? data.items
            : Object.values(data.items);
  
          if (items.length === 0) {
            orderSummary.innerHTML = '<p>Your cart is empty.</p>';
          } else {
            const frag = document.createDocumentFragment();
            items.forEach(item => {
              const div = document.createElement('div');
              div.className = 'flex justify-between';
              div.innerHTML = `
                <span>${item.name} × ${item.quantity}</span>
                <span>$${(item.price * item.quantity).toFixed(2)}</span>
              `;
              frag.appendChild(div);
            });
            orderSummary.innerHTML = '';
            orderSummary.appendChild(frag);
          }
          orderTotal.textContent = data.total.toFixed(2);
        } catch (err) {
          console.error('Order summary load error:', err);
          orderSummary.innerHTML = '<p>Error loading cart summary.</p>';
        }
      })();
    }
  
    // 2. Handle Checkout Form submit only if form exists
    if (form) {
      form.addEventListener('submit', async e => {
        e.preventDefault();
        const payload = {
          name:    form.name.value.trim(),
          address: form.address.value.trim(),
          phone:   form.phone.value.trim()
        };
  
        try {
          const res = await fetch('/cart/checkout', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
          });
  
          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || 'Checkout failed');
          }
  
          const { order_id } = await res.json();
          window.location.href = `/pay/${order_id}`;
        } catch (err) {
          showToast(err.message || 'Checkout Error', 'error');
        }
      });
    }
  });
  