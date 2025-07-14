/**
 * QR Health Data Generator
 * Handles the multi-step form for generating emergency health QR codes
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const form = document.getElementById('qrHealthForm');
    const nextButtons = document.querySelectorAll('.btn-next');
    const prevButtons = document.querySelectorAll('.btn-prev');
    const stepIndicators = document.querySelectorAll('.step');
    const formSteps = document.querySelectorAll('.form-step');
    const accessLevelRadios = document.querySelectorAll('input[name="accessLevel"]');
    const expiryRadios = document.querySelectorAll('input[name="expiry"]');
    const cardOptions = document.querySelectorAll('.card-option');
    const photoUpload = document.getElementById('photoUpload');
    const photoPreview = document.getElementById('photoPreview');
    const photoContainer = document.getElementById('photoContainer');
    const generateBtn = document.getElementById('generateQrBtn');
    const qrPreview = document.getElementById('qrPreview');
    const downloadQrBtn = document.getElementById('downloadQrBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    
    let currentStep = 0;
    
    // Initialize form validation
    if (form) {
        // Initialize form data object
        const formData = {
            profile: {},
            accessLevel: 'basic',
            expiry: '24h',
            cardStyle: 'fridge',
            photo: null
        };
        
        // Initialize form steps
        showStep(currentStep);
        
        // Next button click handler
        nextButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Validate current step before proceeding
                if (validateStep(currentStep)) {
                    // Save step data
                    saveStepData(currentStep);
                    
                    // Move to next step
                    currentStep++;
                    showStep(currentStep);
                    
                    // If this is the last step, generate QR code
                    if (currentStep === formSteps.length - 1) {
                        generateQrCode();
                    }
                }
            });
        });
        
        // Previous button click handler
        prevButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                currentStep--;
                showStep(currentStep);
            });
        });
        
        // Access level selection
        accessLevelRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                formData.accessLevel = this.value;
                updateAccessLevelInfo(this.value);
            });
        });
        
        // Expiry selection
        expiryRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                formData.expiry = this.value;
            });
        });
        
        // Card style selection
        cardOptions.forEach(option => {
            option.addEventListener('click', function() {
                cardOptions.forEach(opt => opt.classList.remove('active'));
                this.classList.add('active');
                formData.cardStyle = this.dataset.style;
                
                // Show/hide photo upload based on selection
                if (formData.cardStyle === 'family') {
                    photoContainer.classList.remove('d-none');
                } else {
                    photoContainer.classList.add('d-none');
                }
            });
        });
        
        // Photo upload
        if (photoUpload) {
            photoUpload.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        photoPreview.src = e.target.result;
                        photoPreview.style.display = 'block';
                        formData.photo = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            // Drag and drop for photo upload
            const dropArea = document.querySelector('.photo-upload-area');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropArea.classList.add('drag-over');
            }
            
            function unhighlight() {
                dropArea.classList.remove('drag-over');
            }
            
            dropArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const file = dt.files[0];
                
                if (file && file.type.match('image.*')) {
                    photoUpload.files = dt.files;
                    const event = new Event('change');
                    photoUpload.dispatchEvent(event);
                }
            }
        }
        
        // Generate QR button
        if (generateBtn) {
            generateBtn.addEventListener('click', generateQrCode);
        }
        
        // Download buttons
        if (downloadQrBtn) {
            downloadQrBtn.addEventListener('click', downloadQrCode);
        }
        
        if (downloadPdfBtn) {
            downloadPdfBtn.addEventListener('click', downloadPdf);
        }
    }
    
    // Show current step and update progress
    function showStep(stepIndex) {
        // Hide all steps
        formSteps.forEach(step => {
            step.classList.remove('active');
        });
        
        // Show current step
        formSteps[stepIndex].classList.add('active');
        
        // Update step indicators
        stepIndicators.forEach((indicator, index) => {
            if (index === stepIndex) {
                indicator.classList.add('active');
            } else if (index < stepIndex) {
                indicator.classList.remove('active');
                indicator.classList.add('completed');
            } else {
                indicator.classList.remove('active', 'completed');
            }
        });
        
        // Show/hide navigation buttons
        const prevButtons = document.querySelectorAll('.btn-prev');
        const nextButtons = document.querySelectorAll('.btn-next');
        
        if (stepIndex === 0) {
            prevButtons.forEach(btn => btn.classList.add('d-none'));
        } else {
            prevButtons.forEach(btn => btn.classList.remove('d-none'));
        }
        
        if (stepIndex === formSteps.length - 1) {
            nextButtons.forEach(btn => btn.classList.add('d-none'));
        } else {
            nextButtons.forEach(btn => btn.classList.remove('d-none'));
        }
        
        // Scroll to top of form
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Validate current step before proceeding
    function validateStep(stepIndex) {
        let isValid = true;
        const currentStep = formSteps[stepIndex];
        const requiredFields = currentStep.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                
                // Add error message if not already present
                if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'This field is required';
                    field.parentNode.insertBefore(errorDiv, field.nextSibling);
                }
            } else {
                field.classList.remove('is-invalid');
                
                // Remove error message if exists
                if (field.nextElementSibling && field.nextElementSibling.classList.contains('invalid-feedback')) {
                    field.nextElementSibling.remove();
                }
                
                // Additional validation for specific fields
                if (field.type === 'email' && !isValidEmail(field.value)) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'Please enter a valid email address';
                    field.parentNode.insertBefore(errorDiv, field.nextSibling);
                }
                
                if (field.type === 'tel' && !isValidPhone(field.value)) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'Please enter a valid phone number';
                    field.parentNode.insertBefore(errorDiv, field.nextSibling);
                }
            }
        });
        
        return isValid;
    }
    
    // Save data from current step
    function saveStepData(stepIndex) {
        const currentStep = formSteps[stepIndex];
        const inputs = currentStep.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (input.type === 'radio' || input.type === 'checkbox') {
                if (input.checked) {
                    formData[input.name] = input.value;
                }
            } else if (input.type !== 'file' && input.type !== 'button' && input.type !== 'submit') {
                // Handle nested objects in form data (e.g., profile.name)
                const nameParts = input.name.split('.');
                if (nameParts.length > 1) {
                    let obj = formData;
                    for (let i = 0; i < nameParts.length - 1; i++) {
                        if (!obj[nameParts[i]]) {
                            obj[nameParts[i]] = {};
                        }
                        obj = obj[nameParts[i]];
                    }
                    obj[nameParts[nameParts.length - 1]] = input.value;
                } else {
                    formData[input.name] = input.value;
                }
            }
        });
        
        console.log('Form data updated:', formData);
    }
    
    // Update access level information
    function updateAccessLevelInfo(level) {
        const basicInfo = document.getElementById('basicAccessInfo');
        const fullInfo = document.getElementById('fullAccessInfo');
        
        if (level === 'basic') {
            basicInfo.classList.remove('d-none');
            fullInfo.classList.add('d-none');
        } else {
            basicInfo.classList.add('d-none');
            fullInfo.classList.remove('d-none');
        }
    }
    
    // Generate QR code
    function generateQrCode() {
        // In a real app, this would make an API call to generate the QR code
        // For now, we'll simulate it with a sample QR code
        const qrContainer = document.getElementById('qrCodeContainer');
        
        if (qrContainer) {
            qrContainer.innerHTML = `
                <div class="text-center">
                    <div class="qr-placeholder bg-light p-4 d-inline-block mb-3">
                        <i class="bi bi-qr-code" style="font-size: 10rem; color: #001689;"></i>
                    </div>
                    <p class="text-muted">Your QR code will be generated here with the selected information.</p>
                </div>
            `;
        }
        
        // Show download buttons
        const downloadButtons = document.getElementById('downloadButtons');
        if (downloadButtons) {
            downloadButtons.classList.remove('d-none');
        }
        
        // Scroll to QR code
        setTimeout(() => {
            qrContainer.scrollIntoView({ behavior: 'smooth' });
        }, 500);
    }
    
    // Download QR code as image
    function downloadQrCode() {
        // In a real app, this would download the actual QR code image
        alert('In a real implementation, this would download the QR code as an image.');
    }
    
    // Download PDF
    function downloadPdf() {
        // In a real app, this would generate and download a PDF
        alert('In a real implementation, this would generate and download a PDF.');
    }
    
    // Helper function to validate email
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    }
    
    // Helper function to validate phone number
    function isValidPhone(phone) {
        const re = /^[+\d\s-()]{10,}$/;
        return re.test(phone);
    }
});
