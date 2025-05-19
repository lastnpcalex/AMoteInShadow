
// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize sidebar toggle
  initSidebarToggle();
  
  // Initialize theme toggle
  initThemeToggle();
  
  // Initialize image handling
  initImageHandling();
});

// Initialize sidebar toggle functionality
function initSidebarToggle() {
  const menuToggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function() {
      sidebar.classList.toggle('active');
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
      if (window.innerWidth <= 768 && 
          !sidebar.contains(event.target) && 
          event.target !== menuToggle) {
        sidebar.classList.remove('active');
      }
    });
  }
}

// Initialize theme toggle functionality
function initThemeToggle() {
  const themeToggle = document.querySelector('.theme-toggle');
  
  if (themeToggle) {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      document.body.setAttribute('data-theme', savedTheme);
    }
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', function() {
      const currentTheme = document.body.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.body.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }
}

// Initialize image handling functionality
function initImageHandling() {
  const images = document.querySelectorAll('.novel-image');
  const imageOverlay = document.querySelector('.image-overlay');
  
  if (images.length > 0 && imageOverlay) {
    images.forEach(image => {
      // Add click handler to expand/rotate images
      image.addEventListener('click', function() {
        this.classList.toggle('expanded');
        imageOverlay.classList.toggle('active');
      });
    });
    
    // Add click handler to close expanded images
    imageOverlay.addEventListener('click', function() {
      const expandedImage = document.querySelector('.novel-image.expanded');
      if (expandedImage) {
        expandedImage.classList.remove('expanded');
        imageOverlay.classList.remove('active');
      }
    });
  }
}
