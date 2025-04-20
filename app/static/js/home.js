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