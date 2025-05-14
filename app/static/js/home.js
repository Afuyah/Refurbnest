document.addEventListener('DOMContentLoaded', () => {
    // Animate elements using Intersection Observer
    const animateOnScroll = (elements) => {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
          }
        });
      }, { threshold: 0.1 });
  
      elements.forEach(el => observer.observe(el));
    };
  
    // Animate cards
    animateOnScroll(document.querySelectorAll('.card'));
    
    // Animate stats
    animateOnScroll(document.querySelectorAll('.glass-effect'));
  });


  document.addEventListener('DOMContentLoaded', () => {
    new Swiper('.featured-swiper', {
      slidesPerView: 1,
      spaceBetween: 20,
      loop: true,
      autoplay: { delay: 3000, disableOnInteraction: false },
      pagination: { el: '.swiper-pagination', clickable: true },
      navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
      breakpoints: {
        576: { slidesPerView: 2, spaceBetween: 20 },
        992: { slidesPerView: 3, spaceBetween: 30 },
      },
    });
  });
  




 // Enhanced mobile menu functionality
        document.addEventListener('DOMContentLoaded', () => {
            const navbarCollapse = document.querySelector('.navbar-collapse');

            // Close menu when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.navbar') && navbarCollapse.classList.contains('show')) {
                    navbarCollapse.classList.remove('show');
                }
            });

            // Dynamic navbar scroll effect
            window.addEventListener('scroll', () => {
                const navbar = document.querySelector('.navbar');
                navbar.classList.toggle('scrolled', window.scrollY > 50);
            });
        });






  document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('offers-grid');
  const tpl  = document.getElementById('offer-card-template').content;

  async function loadOffers() {
    try {
      const res = await fetch('/api/featured-products');
      if (!res.ok) throw new Error('Network error');
      const products = await res.json();

      if (!products.length) {
        grid.innerHTML = '<p class="text-center">No offers available</p>';
        return;
      }

      // Only show up to 8
      products.slice(0, 8).forEach(p => {
        const clone = document.importNode(tpl, true);

        // Media
        const img = clone.querySelector('.offer-image');
        img.src = p.image;
        img.alt = p.name;
        const viewLink = clone.querySelector('.offer-view-btn');
        viewLink.href = `/products/${p.id}`;   
        viewLink.textContent = 'View Deal';

        // Body
        clone.querySelector('.offer-title').textContent = p.name;
        clone.querySelector('.offer-price').textContent = `$${p.price.toFixed(2)}`;

        // Original price & discount
        if (p.original_price) {
          const op = clone.querySelector('.offer-original-price');
          op.textContent = `$${p.original_price.toFixed(2)}`;
          op.classList.remove('d-none');

          const discount = Math.round((1 - (p.price / p.original_price)) * 100);
          clone.querySelector('.discount-percent').textContent = `Save ${discount}%`;
        } else {
          clone.querySelector('.discount-percent').textContent = '';
        }

        // Static rating or from API
        clone.querySelector('.rating-value').textContent = p.rating || '4.8';

        grid.appendChild(clone);
      });

    } catch (err) {
      console.error('Could not load offers', err);
      grid.innerHTML = '<p class="text-center text-danger">Failed to load offers.</p>';
    }
  }

  loadOffers();
});







  


  // Animate number counters
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count)
    const duration = 2000
    const start = Date.now()
    
    const update = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      el.textContent = (progress * target).toFixed(progress > 0.99 ? 0 : 1)
      
      if (progress < 1) requestAnimationFrame(update)
    }
    
    requestAnimationFrame(update)
  })
  
  // Initialize animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible')
      }
    })
  }, { threshold: 0.1 })
  
  document.querySelectorAll('.hover-lift').forEach(el => observer.observe(el))
  
  
  
  document.addEventListener('DOMContentLoaded', () => {
    const totalSlides = {{ featured_products|length }};
    new Swiper('.featured-swiper', {
      loop: true,
      autoplay: {
        delay: 3000,
        disableOnInteraction: false
      },
      pagination: {
        el: '.swiper-pagination',
        clickable: true
      },
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev'
      },
      // Automatically fill blanks if slide count < group size
      loopFillGroupWithBlank: true,
      // Responsive breakpoints with capping
      breakpoints: {
        576: {
          slidesPerView: Math.min(2, totalSlides),
          slidesPerGroup: Math.min(2, totalSlides)
        },
        992: {
          slidesPerView: Math.min(3, totalSlides),
          slidesPerGroup: Math.min(3, totalSlides)
        }
      },
      // Mobile default
      slidesPerView: Math.min(1, totalSlides),
      slidesPerGroup: Math.min(1, totalSlides)
    });
    console.log('Swiper initialized with', totalSlides, 'slides');
  });
  
  
  
  