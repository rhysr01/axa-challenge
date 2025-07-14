/**
 * AXA ADAPT - Card Personalization
 * Handles card personalization functionality including:
 * - Background image upload and preview
 * - Preset background selection
 * - Color scheme customization
 * - Text customization
 * - Live preview updates
 */

document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const cardPersonalization = document.querySelector('.card-personalization');
  const cardPreview = document.querySelector('.card-preview');
  const uploadPreview = document.querySelector('.upload-preview');
  const fileInput = document.querySelector('#background-upload');
  const presetBackgrounds = document.querySelectorAll('.preset-bg');
  const colorOptions = document.querySelectorAll('.color-option');
  const titleInput = document.querySelector('#card-title');
  const subtitleInput = document.querySelector('#card-subtitle');
  const resetButton = document.querySelector('.btn-reset');
  const saveButton = document.querySelector('.btn-save');
  const printButton = document.querySelector('.btn-print');
  
  // Default values
  const defaultValues = {
    backgroundImage: '',
    backgroundColor: '#0066CC',
    title: 'Emergency Health Information',
    subtitle: 'Scan this QR code to view my health information',
    textColor: '#FFFFFF',
    qrCode: '/static/img/qr-placeholder.png' // Default QR code
  };
  
  // Current state
  let currentState = { ...defaultValues };
  
  // Initialize
  function init() {
    // Load saved preferences if available
    loadSavedPreferences();
    
    // Set up event listeners
    setupEventListeners();
    
    // Update preview with current state
    updatePreview();
  }
  
  // Load saved preferences from localStorage
  function loadSavedPreferences() {
    const savedState = localStorage.getItem('axaCardPersonalization');
    if (savedState) {
      try {
        const parsedState = JSON.parse(savedState);
        currentState = { ...defaultValues, ...parsedState };
        
        // Update form fields
        if (titleInput) titleInput.value = currentState.title;
        if (subtitleInput) subtitleInput.value = currentState.subtitle;
        
        // Update active states
        updateActiveStates();
      } catch (e) {
        console.error('Error loading saved preferences:', e);
        localStorage.removeItem('axaCardPersonalization');
      }
    }
  }
  
  // Save current state to localStorage
  function savePreferences() {
    try {
      localStorage.setItem('axaCardPersonalization', JSON.stringify(currentState));
      showToast('Preferences saved successfully!');
    } catch (e) {
      console.error('Error saving preferences:', e);
      showToast('Error saving preferences', 'error');
    }
  }
  
  // Set up event listeners
  function setupEventListeners() {
    // File upload
    if (uploadPreview) {
      uploadPreview.addEventListener('click', () => fileInput.click());
    }
    
    if (fileInput) {
      fileInput.addEventListener('change', handleFileUpload);
    }
    
    // Preset backgrounds
    presetBackgrounds.forEach(bg => {
      bg.addEventListener('click', () => {
        const bgImage = bg.getAttribute('data-bg-image');
        if (bgImage) {
          currentState.backgroundImage = `url('${bgImage}')`;
          updatePreview();
          
          // Update active state
          presetBackgrounds.forEach(b => b.classList.remove('active'));
          bg.classList.add('active');
          
          // Reset file input
          if (fileInput) fileInput.value = '';
          if (uploadPreview) {
            uploadPreview.style.backgroundImage = '';
            uploadPreview.classList.remove('has-image');
          }
        }
      });
    });
    
    // Color options
    colorOptions.forEach(color => {
      color.addEventListener('click', () => {
        const colorValue = color.getAttribute('data-color');
        const colorType = color.getAttribute('data-color-type');
        
        if (colorType === 'background') {
          currentState.backgroundColor = colorValue;
          currentState.backgroundImage = ''; // Reset background image when solid color is selected
          
          // Reset active states for preset backgrounds
          presetBackgrounds.forEach(bg => bg.classList.remove('active'));
          
          // Reset file input
          if (fileInput) fileInput.value = '';
          if (uploadPreview) {
            uploadPreview.style.backgroundImage = '';
            uploadPreview.classList.remove('has-image');
          }
        } else if (colorType === 'text') {
          currentState.textColor = colorValue;
        }
        
        updatePreview();
        updateActiveStates();
      });
    });
    
    // Text inputs
    if (titleInput) {
      titleInput.addEventListener('input', (e) => {
        currentState.title = e.target.value || defaultValues.title;
        updatePreview();
      });
    }
    
    if (subtitleInput) {
      subtitleInput.addEventListener('input', (e) => {
        currentState.subtitle = e.target.value || defaultValues.subtitle;
        updatePreview();
      });
    }
    
    // Buttons
    if (resetButton) {
      resetButton.addEventListener('click', resetToDefaults);
    }
    
    if (saveButton) {
      saveButton.addEventListener('click', savePreferences);
    }
    
    if (printButton) {
      printButton.addEventListener('click', () => window.print());
    }
  }
  
  // Handle file upload
  function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Check file type
    if (!file.type.match('image.*')) {
      showToast('Please select a valid image file', 'error');
      return;
    }
    
    // Check file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      showToast('Image size should be less than 2MB', 'error');
      return;
    }
    
    const reader = new FileReader();
    
    reader.onload = function(event) {
      const imageUrl = event.target.result;
      currentState.backgroundImage = `url('${imageUrl}')`;
      
      // Update preview
      updatePreview();
      
      // Update upload preview
      if (uploadPreview) {
        uploadPreview.style.backgroundImage = `url('${imageUrl}')`;
        uploadPreview.classList.add('has-image');
      }
      
      // Reset active states for preset backgrounds
      presetBackgrounds.forEach(bg => bg.classList.remove('active'));
    };
    
    reader.readAsDataURL(file);
  }
  
  // Update active states for UI elements
  function updateActiveStates() {
    // Update color options
    colorOptions.forEach(color => {
      const colorType = color.getAttribute('data-color-type');
      const colorValue = color.getAttribute('data-color');
      
      if ((colorType === 'background' && colorValue === currentState.backgroundColor) ||
          (colorType === 'text' && colorValue === currentState.textColor)) {
        color.classList.add('active');
      } else {
        color.classList.remove('active');
      }
    });
  }
  
  // Update card preview
  function updatePreview() {
    if (!cardPreview) return;
    
    // Set background
    if (currentState.backgroundImage) {
      cardPreview.style.backgroundImage = currentState.backgroundImage;
      cardPreview.style.backgroundColor = '';
    } else {
      cardPreview.style.backgroundImage = '';
      cardPreview.style.backgroundColor = currentState.backgroundColor;
    }
    
    // Set text color
    cardPreview.style.color = currentState.textColor;
    
    // Update title and subtitle
    const titleElement = cardPreview.querySelector('.card-preview-title-text');
    const subtitleElement = cardPreview.querySelector('.card-preview-subtitle');
    
    if (titleElement) titleElement.textContent = currentState.title;
    if (subtitleElement) subtitleElement.textContent = currentState.subtitle;
    
    // Update QR code if available
    const qrElement = cardPreview.querySelector('.card-preview-qr img');
    if (qrElement && currentState.qrCode) {
      qrElement.src = currentState.qrCode;
    }
  }
  
  // Reset to default values
  function resetToDefaults() {
    if (confirm('Are you sure you want to reset all customizations?')) {
      currentState = { ...defaultValues };
      
      // Reset form fields
      if (titleInput) titleInput.value = currentState.title;
      if (subtitleInput) subtitleInput.value = currentState.subtitle;
      
      // Reset file input
      if (fileInput) fileInput.value = '';
      if (uploadPreview) {
        uploadPreview.style.backgroundImage = '';
        uploadPreview.classList.remove('has-image');
      }
      
      // Reset active states
      presetBackgrounds.forEach(bg => bg.classList.remove('active'));
      
      // Update preview
      updatePreview();
      updateActiveStates();
      
      showToast('All customizations have been reset');
    }
  }
  
  // Show toast notification
  function showToast(message, type = 'success') {
    // You can implement a toast notification system here
    // For now, we'll just use a simple alert
    alert(message);
  }
  
  // Initialize the card personalization
  if (cardPersonalization) {
    init();
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
