/**
 * AXA ADAPT - Header Navigation
 * Handles mobile menu toggle and dropdown functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const header = document.querySelector('.header');
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const nav = document.querySelector('.nav');
  const navLinks = document.querySelectorAll('.nav-link');
  const dropdownToggles = document.querySelectorAll('.dropdown > .nav-link');
  
  // Check if mobile menu should be active
  const isMobile = () => window.innerWidth < 992;
  
  // Toggle mobile menu
  function toggleMobileMenu(forceClose = false) {
    const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
    const shouldClose = forceClose || isExpanded;
    
    // Update button state
    mobileMenuBtn.setAttribute('aria-expanded', !shouldClose);
    mobileMenuBtn.setAttribute('aria-label', shouldClose ? 'Open menu' : 'Close menu');
    
    // Toggle menu visibility
    if (shouldClose) {
      nav.classList.remove('active');
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    } else {
      nav.classList.add('active');
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    }
  }
  
  // Toggle dropdown menu
  function toggleDropdown(dropdown, forceClose = false) {
    const isExpanded = dropdown.getAttribute('data-expanded') === 'true';
    const shouldClose = forceClose || isExpanded;
    
    // Update dropdown state
    dropdown.setAttribute('data-expanded', !shouldClose);
    const toggle = dropdown.querySelector('> .nav-link');
    
    if (toggle) {
      toggle.setAttribute('aria-expanded', !shouldClose);
    }
  }
  
  // Close all dropdowns except the one being toggled
  function closeOtherDropdowns(currentDropdown) {
    document.querySelectorAll('.dropdown').forEach(dropdown => {
      if (dropdown !== currentDropdown && dropdown.getAttribute('data-expanded') === 'true') {
        toggleDropdown(dropdown, true);
      }
    });
  }
  
  // Handle window resize
  function handleResize() {
    if (!isMobile()) {
      // Reset mobile menu state on desktop
      if (nav.classList.contains('active')) {
        toggleMobileMenu(true);
      }
      
      // Close all dropdowns on desktop when clicking outside
      document.removeEventListener('click', handleOutsideClick);
    } else {
      // Add click outside handler for mobile
      document.addEventListener('click', handleOutsideClick);
    }
  }
  
  // Handle clicks outside the navigation
  function handleOutsideClick(e) {
    if (!nav.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
      // Close mobile menu if open
      if (nav.classList.contains('active')) {
        toggleMobileMenu(true);
      }
      
      // Close all dropdowns
      document.querySelectorAll('.dropdown').forEach(dropdown => {
        toggleDropdown(dropdown, true);
      });
    }
  }
  
  // Add scroll effect to header
  function handleScroll() {
    if (window.scrollY > 20) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }
  
  // Event Listeners
  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMobileMenu();
    });
  }
  
  // Handle dropdown toggles
  dropdownToggles.forEach(toggle => {
    const dropdown = toggle.parentElement;
    
    toggle.addEventListener('click', (e) => {
      // Only handle dropdown toggle on mobile or if it's a mobile device
      if (isMobile()) {
        e.preventDefault();
        e.stopPropagation();
        closeOtherDropdowns(dropdown);
        toggleDropdown(dropdown);
      }
    });
    
    // Handle keyboard navigation
    toggle.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        closeOtherDropdowns(dropdown);
        toggleDropdown(dropdown);
      } else if (e.key === 'Escape') {
        toggleDropdown(dropdown, true);
      }
    });
  });
  
  // Close dropdowns when clicking on a nav link (for mobile)
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      if (isMobile() && !link.classList.contains('dropdown-toggle')) {
        toggleMobileMenu(true);
      }
    });
  });
  
  // Close dropdowns when clicking outside (desktop)
  if (!isMobile()) {
    document.addEventListener('click', (e) => {
      const isClickInside = nav.contains(e.target) || 
                          mobileMenuBtn.contains(e.target) ||
                          e.target.closest('.dropdown');
      
      if (!isClickInside) {
        document.querySelectorAll('.dropdown').forEach(dropdown => {
          toggleDropdown(dropdown, true);
        });
      }
    });
  }
  
  // Initialize
  handleScroll();
  handleResize();
  
  // Add event listeners
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('resize', handleResize);
  
  // Close menu when pressing Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (nav.classList.contains('active')) {
        toggleMobileMenu(true);
      }
      
      // Close all dropdowns
      document.querySelectorAll('.dropdown').forEach(dropdown => {
        toggleDropdown(dropdown, true);
      });
    }
  });
  
  // Handle focus trap for mobile menu
  if (isMobile()) {
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableContent = nav.querySelectorAll(focusableElements);
    const firstFocusableElement = focusableContent[0];
    const lastFocusableElement = focusableContent[focusableContent.length - 1];
    
    nav.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusableElement) {
            lastFocusableElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusableElement) {
            firstFocusableElement.focus();
            e.preventDefault();
          }
        }
      }
    });
  }
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    init: function() {
      // This allows the script to be imported and initialized manually
      document.dispatchEvent(new Event('DOMContentLoaded'));
    }
  };
}
