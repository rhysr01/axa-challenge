/**
 * QR Health Data Form Validation
 * Provides real-time validation and feedback for the QR Health Data form
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('qrHealthForm');
    if (!form) return;

    // Form fields that require validation
    const requiredFields = form.querySelectorAll('[required]');
    const emailFields = form.querySelectorAll('input[type="email"]');
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    const dateFields = form.querySelectorAll('input[type="date"]');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(form.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus'
        });
    });

    // Add validation classes on blur
    requiredFields.forEach(field => {
        field.addEventListener('blur', validateField);
        field.addEventListener('input', clearValidation);
    });

    // Email validation
    emailFields.forEach(emailField => {
        emailField.addEventListener('blur', validateEmail);
        emailField.addEventListener('input', clearValidation);
    });

    // Phone validation
    phoneFields.forEach(phoneField => {
        phoneField.addEventListener('blur', validatePhone);
        phoneField.addEventListener('input', clearValidation);
    });

    // Date validation
    dateFields.forEach(dateField => {
        dateField.addEventListener('change', validateDate);
        dateField.addEventListener('input', clearValidation);
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate all fields before submission
        let isValid = true;
        requiredFields.forEach(field => {
            if (!validateField({ target: field })) {
                isValid = false;
            }
        });

        if (isValid) {
            // Show success feedback
            showFormFeedback('Form submitted successfully!', 'success');
            
            // In a real app, you would submit the form here
            // form.submit();
        } else {
            showFormFeedback('Please correct the errors in the form.', 'error');
        }
    });

    // Field validation functions
    function validateField(e) {
        const field = e.target;
        const value = field.value.trim();
        let isValid = true;
        
        // Clear previous validation classes
        clearFieldValidation(field);
        
        // Check required fields
        if (field.required && !value) {
            showFieldError(field, 'This field is required');
            return false;
        }
        
        // Additional validation based on field type
        if (field.type === 'email' && value) {
            isValid = validateEmail({ target: field });
        } else if (field.type === 'tel' && value) {
            isValid = validatePhone({ target: field });
        } else if (field.type === 'date' && value) {
            isValid = validateDate({ target: field });
        }
        
        // If the field is valid, add success styling
        if (isValid && value) {
            field.classList.add('is-valid');
            
            // Add success feedback icon
            const feedback = document.createElement('div');
            feedback.className = 'valid-feedback';
            feedback.textContent = 'Looks good!';
            
            const parent = field.closest('.form-group') || field.parentNode;
            parent.appendChild(feedback);
        }
        
        return isValid;
    }
    
    function validateEmail(e) {
        const field = e.target;
        const email = field.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email && !emailRegex.test(email)) {
            showFieldError(field, 'Please enter a valid email address');
            return false;
        }
        
        return true;
    }
    
    function validatePhone(e) {
        const field = e.target;
        const phone = field.value.trim();
        // Basic phone validation - allows numbers, spaces, +, -, (, )
        const phoneRegex = /^[0-9\s+\-()]*$/;
        
        if (phone && !phoneRegex.test(phone)) {
            showFieldError(field, 'Please enter a valid phone number');
            return false;
        }
        
        return true;
    }
    
    function validateDate(e) {
        const field = e.target;
        const dateValue = field.value;
        
        if (!dateValue) return true;
        
        const date = new Date(dateValue);
        const today = new Date();
        
        // Check if it's a valid date
        if (isNaN(date.getTime())) {
            showFieldError(field, 'Please enter a valid date');
            return false;
        }
        
        // For date of birth, check if it's in the past
        if (field.id === 'dateOfBirth' && date > today) {
            showFieldError(field, 'Birth date cannot be in the future');
            return false;
        }
        
        return true;
    }
    
    // Helper functions
    function showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        // Remove any existing error messages
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // Add error message
        const error = document.createElement('div');
        error.className = 'invalid-feedback';
        error.textContent = message;
        
        const parent = field.closest('.form-group') || field.parentNode;
        parent.appendChild(error);
    }
    
    function clearFieldValidation(field) {
        field.classList.remove('is-invalid', 'is-valid');
        
        // Remove any existing feedback messages
        const parent = field.closest('.form-group') || field.parentNode;
        const invalidFeedback = parent.querySelector('.invalid-feedback');
        const validFeedback = parent.querySelector('.valid-feedback');
        
        if (invalidFeedback) invalidFeedback.remove();
        if (validFeedback) validFeedback.remove();
    }
    
    function clearValidation(e) {
        const field = e.target;
        clearFieldValidation(field);
    }
    
    function showFormFeedback(message, type = 'success') {
        // Remove any existing alerts
        const existingAlert = document.querySelector('.form-feedback');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} form-feedback mt-3`;
        alert.role = 'alert';
        alert.textContent = message;
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('data-bs-dismiss', 'alert');
        closeBtn.setAttribute('aria-label', 'Close');
        alert.appendChild(closeBtn);
        
        // Insert after the form
        form.parentNode.insertBefore(alert, form.nextSibling);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    }
    
    // Initialize form validation on step changes
    const nextButtons = form.querySelectorAll('.btn-next');
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = this.closest('.form-step');
            const nextStepId = this.getAttribute('data-next');
            
            if (nextStepId) {
                // Validate current step before proceeding
                const fields = currentStep.querySelectorAll('[required]');
                let isValid = true;
                
                fields.forEach(field => {
                    if (!validateField({ target: field })) {
                        isValid = false;
                    }
                });
                
                if (isValid) {
                    // Hide current step and show next step
                    currentStep.classList.add('d-none');
                    document.getElementById(nextStepId).classList.remove('d-none');
                    
                    // Update progress indicator
                    updateProgressIndicator(nextStepId);
                    
                    // Scroll to top of the form
                    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    // Scroll to first error
                    const firstError = form.querySelector('.is-invalid');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstError.focus();
                    }
                }
            }
        });
    });
    
    // Back button functionality
    const prevButtons = form.querySelectorAll('.btn-prev');
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = this.closest('.form-step');
            const prevStepId = this.getAttribute('data-prev');
            
            if (prevStepId) {
                currentStep.classList.add('d-none');
                document.getElementById(prevStepId).classList.remove('d-none');
                
                // Update progress indicator
                updateProgressIndicator(prevStepId);
                
                // Scroll to top of the form
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Update progress indicator
    function updateProgressIndicator(activeStepId) {
        const activeStepNumber = parseInt(activeStepId.replace('step', ''));
        const steps = form.querySelectorAll('.step');
        
        steps.forEach((step, index) => {
            const stepNumber = parseInt(step.getAttribute('data-step'));
            
            if (stepNumber < activeStepNumber) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (stepNumber === activeStepNumber) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }
    
    // Toggle emergency contact fields
    const emergencyToggle = form.querySelector('#emergencyContactToggle');
    const emergencyFields = form.querySelector('#emergencyContactFields');
    
    if (emergencyToggle && emergencyFields) {
        emergencyToggle.addEventListener('change', function() {
            if (this.checked) {
                emergencyFields.classList.remove('d-none');
            } else {
                emergencyFields.classList.add('d-none');
            }
        });
    }
});
