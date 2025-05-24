// static/js/checkout.js

document.addEventListener('DOMContentLoaded', () => {
  const summaryContainer = document.getElementById('order-summary');
  const totalEl          = document.getElementById('order-total');
  const form             = document.getElementById('checkout-form');
  const csrfToken        = document.querySelector('input[name="csrf_token"]').value;
  const toastContainer   = document.getElementById('toastContainer');

  // — Toast helper —
  function showToast(msg, variant = 'success') {
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
      <div class="toast align-items-center text-bg-${variant} border-0 mb-2" 
           role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">${msg}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                  data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>`;
    const toastEl = wrapper.firstElementChild;
    toastContainer.appendChild(toastEl);
    new bootstrap.Toast(toastEl, { delay: 4000 }).show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
  }

  // — Render the summary —
  function renderSummary(items, total) {
    if (!items || items.length === 0) {
      summaryContainer.innerHTML = '<p>Your cart is empty.</p>';
      totalEl.textContent = '0.00';
      return;
    }

    summaryContainer.innerHTML = '';
    items.forEach(item => {
      const row = document.createElement('div');
      row.className = 'd-flex justify-content-between mb-3';
      row.innerHTML = `
        <div class="text-black">
          <strong>${item.name}</strong>
          <div class=" text-black">
            ${item.quantity} × $${parseFloat(item.price).toFixed(2)}
          </div>
        </div>
        <div class="text-black">$${(item.quantity * item.price).toFixed(2)}</div>`;
      summaryContainer.appendChild(row);
    });

    totalEl.textContent = parseFloat(total).toFixed(2);
  }

  // — Fetch & display the cart —
  async function loadSummary() {
    summaryContainer.innerHTML = '<p>Loading your cart…</p>';
    try {
      const res  = await fetch('/cart/json', { credentials: 'same-origin' });
      if (!res.ok) throw new Error('Could not load cart summary');
      const data = await res.json();
      renderSummary(data.items, data.total);
    } catch (err) {
      summaryContainer.innerHTML = `<p class="text-danger">${err.message}</p>`;
      totalEl.textContent = '0.00';
    }
  }

  // — Handle form submission —
  form.addEventListener('submit', async e => {
    e.preventDefault();
    e.stopPropagation();

    const btn     = form.querySelector('button[type="submit"]');
    const spinner = btn.querySelector('.loading-spinner');
    const payload = {
      name:    form.name.value.trim(),
      address: form.address.value.trim(),
      zip:     form.zip.value.trim(),
      phone:   form.phone.value.trim()
    };

    if (!payload.name || !payload.address || !payload.phone) {
      return showToast('All fields are required.', 'warning');
    }

    btn.disabled = true;
    spinner.classList.remove('hidden');

    try {
      const res  = await fetch('/cart/checkout', {
        method:      'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  csrfToken
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.description || data.message || 'Checkout failed');

      showToast(data.message, 'success');
      // Redirect to payment page
      window.location.href = data.redirect;
    } catch (err) {
      showToast(err.message, 'danger');
    } finally {
      btn.disabled = false;
      spinner.classList.add('hidden');
    }
  });

  // — Kick things off —
  loadSummary();
});
