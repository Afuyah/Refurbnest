document.addEventListener('DOMContentLoaded', () => {
  // ——————— DOM Caching ———————
  const summaryContainer = document.getElementById('order-summary');
  const totalEl          = document.getElementById('order-total');
  const form             = document.getElementById('checkout-form');
  const csrfToken        = document.querySelector('meta[name="csrf-token"]').content;
  const toastContainer   = document.getElementById('toastContainer');

  // ——————— Toast Helper ———————
  const showToast = (message, type='success') => {
    const toastEl = document.createElement('div');
    toastEl.innerHTML = `
      <div class="toast align-items-center text-bg-${type} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>`;
    const node = toastEl.firstElementChild;
    toastContainer.appendChild(node);
    const bsToast = new bootstrap.Toast(node, { delay: 4000 });
    bsToast.show();
    node.addEventListener('hidden.bs.toast', () => node.remove());
  };

  // ——————— Render Order Summary ———————
  async function loadSummary() {
    summaryContainer.innerHTML = '<p>Loading your cart…</p>';
    try {
      const res = await fetch('/cart/summary', { credentials: 'same-origin' });
      if (!res.ok) throw new Error('Could not load cart summary');
      const data = await res.json();
      renderSummary(data.items, data.total);
    } catch (err) {
      summaryContainer.innerHTML = `<p class="text-danger">${err.message}</p>`;
    }
  }

  function renderSummary(items, total) {
    if (!items || Object.keys(items).length === 0) {
      summaryContainer.innerHTML = '<p>Your cart is empty.</p>';
      totalEl.textContent = '0.00';
      return;
    }

    // Build list
    summaryContainer.innerHTML = '';
    Object.values(items).forEach(item => {
      const div = document.createElement('div');
      div.className = 'd-flex justify-content-between';
      div.innerHTML = `
        <div>
          <strong>${item.name}</strong>
          <div class="small text-muted">
            ${item.quantity} × $${parseFloat(item.price).toFixed(2)}
          </div>
        </div>
        <div>
          $${(item.quantity * item.price).toFixed(2)}
        </div>`;
      summaryContainer.appendChild(div);
    });

    totalEl.textContent = parseFloat(total).toFixed(2);
  }

  // ——————— Form Submission ———————
  form.addEventListener('submit', async e => {
    e.preventDefault();

    const payload = {
      name:    form.name.value.trim(),
      address: form.address.value.trim(),
      zip:     form.zip ? form.zip.value.trim() : '',
      phone:   form.phone.value.trim()
    };

    // Basic client-side validation
    if (!payload.name || !payload.address || !payload.phone) {
      showToast('Please fill in all required fields.', 'warning');
      return;
    }

    // Disable button to prevent double submissions
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    try {
      const res = await fetch('/checkout', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.description || err.message || 'Checkout failed');
      }

      const data = await res.json();
      showToast(data.message || 'Order placed successfully!', 'success');

      // Redirect to payment page or confirmation
      window.location.href = `/payment/${data.order_id}`;
    } catch (err) {
      showToast(err.message, 'danger');
    } finally {
      submitBtn.disabled = false;
    }
  });

  // ——————— Init ———————
  loadSummary();
});
