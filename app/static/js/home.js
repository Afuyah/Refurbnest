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
  

