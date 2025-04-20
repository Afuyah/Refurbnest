// Initialize Product List Interactions
document.addEventListener('DOMContentLoaded', () => {
    // Lazy Load Images
    const lazyImages = document.querySelectorAll('.lazy-load');
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.add('loaded');
          imageObserver.unobserve(img);
        }
      });
    });
  
    lazyImages.forEach(img => imageObserver.observe(img));
  
    // Filter Products
    const brandFilter = document.getElementById('brand-filter');
    if (brandFilter) {
      brandFilter.addEventListener('change', filterProducts);
    }
  
    // Wishlist Toggle
    document.querySelectorAll('.wishlist-toggle').forEach(button => {
      button.addEventListener('click', function() {
        this.classList.toggle('active');
        // Add API call to update wishlist here
      });
    });
  
    // Initialize Animations
    const animatedElements = document.querySelectorAll('[data-animate]');
    animatedElements.forEach((el, index) => {
      el.style.animationDelay = `${index * 50}ms`;
    });
  });
  
  function filterProducts() {
    const brand = document.getElementById('brand-filter').value;
    const products = document.querySelectorAll('.product-card');
  
    products.forEach(product => {
      const showProduct = !brand || product.dataset.brand === brand;
      product.style.display = showProduct ? 'block' : 'none';
    });
  }