/**
 * Room Scan Mode JavaScript
 * Handles the room scan interface including image uploads and form validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const roomTabs = document.querySelectorAll('.room-tab');
    const uploadForms = document.querySelectorAll('.upload-form');
    const fileInputs = document.querySelectorAll('.file-input');
    const uploadAreas = document.querySelectorAll('.upload-area');
    const startAnalysisBtn = document.getElementById('startAnalysisBtn');
    const healthForm = document.getElementById('healthProfileForm');
    const progressBars = document.querySelectorAll('.progress-bar');
    const uploadStatuses = document.querySelectorAll('.upload-status');
    
    // Track uploaded files by room type
    const uploadedFiles = {
        bedroom: [],
        bathroom: [],
        living: [],
        hallway: [],
        stairs: []
    };
    
    // Track upload progress by room type
    const uploadProgress = {
        bedroom: 0,
        bathroom: 0,
        living: 0,
        hallway: 0,
        stairs: 0
    };
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Room tab switching
    roomTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const roomType = this.getAttribute('data-room');
            
            // Update active tab
            roomTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding upload form
            uploadForms.forEach(form => {
                if (form.id === `${roomType}Upload`) {
                    form.classList.remove('d-none');
                } else {
                    form.classList.add('d-none');
                }
            });
        });
    });
    
    // Handle drag and drop for upload areas
    uploadAreas.forEach(area => {
        const roomType = area.closest('.upload-form').id.replace('Upload', '');
        const fileInput = area.querySelector('.file-input');
        const fileList = area.nextElementSibling;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            area.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        area.addEventListener('drop', handleDrop, false);
        
        // Click to select files
        area.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Handle file selection
        fileInput.addEventListener('change', function(e) {
            handleFiles(e.target.files, roomType, fileList);
        });
    });
    
    // Handle form submission
    healthForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate form
        if (!this.checkValidity()) {
            e.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        
        // Check if at least one room has been uploaded
        const hasUploads = Object.values(uploadedFiles).some(files => files.length > 0);
        
        if (!hasUploads) {
            showAlert('Please upload photos of at least one room before starting the analysis.', 'warning');
            return;
        }
        
        // Show loading state
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing...';
        
        // Simulate analysis (replace with actual API call)
        setTimeout(() => {
            // Redirect to results page
            window.location.href = '/room-scan/results';
        }, 2000);
    });
    
    // Helper Functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        e.target.closest('.upload-area').classList.add('drag-over');
    }
    
    function unhighlight(e) {
        e.target.closest('.upload-area').classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const roomType = e.target.closest('.upload-form').id.replace('Upload', '');
        const fileList = e.target.closest('.upload-form').querySelector('.file-list');
        const dt = e.dataTransfer;
        const files = dt.files;
        
        handleFiles(files, roomType, fileList);
    }
    
    function handleFiles(files, roomType, fileListElement) {
        const roomTypeKey = roomType.toLowerCase();
        
        // Clear existing files for this room
        uploadedFiles[roomTypeKey] = [];
        fileListElement.innerHTML = '';
        
        // Process each file
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Validate file type
            if (!file.type.match('image.*')) {
                showAlert('Only image files are allowed.', 'danger');
                continue;
            }
            
            // Add to uploaded files
            uploadedFiles[roomTypeKey].push(file);
            
            // Create preview
            const reader = new FileReader();
            reader.onload = function(e) {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item d-flex align-items-center mb-2';
                fileItem.innerHTML = `
                    <div class="file-preview me-2" style="width: 50px; height: 50px; overflow: hidden; border-radius: 4px;">
                        <img src="${e.target.result}" alt="Preview" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div class="file-info flex-grow-1">
                        <div class="file-name small text-truncate" style="max-width: 200px;">${file.name}</div>
                        <div class="file-size small text-muted">${formatFileSize(file.size)}</div>
                    </div>
                    <button type="button" class="btn-close" aria-label="Remove"></button>
                `;
                
                // Add remove button handler
                const removeBtn = fileItem.querySelector('.btn-close');
                removeBtn.addEventListener('click', function() {
                    // Remove from array
                    const index = uploadedFiles[roomTypeKey].indexOf(file);
                    if (index > -1) {
                        uploadedFiles[roomTypeKey].splice(index, 1);
                    }
                    
                    // Remove from DOM
                    fileItem.remove();
                    
                    // Update upload status
                    updateUploadStatus(roomTypeKey);
                });
                
                fileListElement.appendChild(fileItem);
            };
            
            reader.readAsDataURL(file);
        }
        
        // Update upload status
        updateUploadStatus(roomTypeKey);
        
        // Simulate upload progress (replace with actual upload)
        simulateUpload(roomTypeKey);
    }
    
    function updateUploadStatus(roomType) {
        const roomTypeKey = roomType.toLowerCase();
        const roomTab = document.querySelector(`.room-tab[data-room="${roomTypeKey}"]`);
        const statusBadge = roomTab.querySelector('.upload-status');
        const fileCount = uploadedFiles[roomTypeKey].length;
        
        if (fileCount > 0) {
            statusBadge.classList.remove('d-none');
            statusBadge.textContent = fileCount;
            statusBadge.classList.add('text-success');
            statusBadge.classList.remove('text-warning');
        } else {
            statusBadge.classList.add('d-none');
        }
        
        // Enable/disable start analysis button
        const hasUploads = Object.values(uploadedFiles).some(files => files.length > 0);
        startAnalysisBtn.disabled = !hasUploads;
    }
    
    function simulateUpload(roomType) {
        const progressBar = document.querySelector(`#${roomType}Upload .progress`);
        const progressFill = document.querySelector(`#${roomType}Upload .progress-bar`);
        
        // Show progress bar
        progressBar.classList.remove('d-none');
        
        // Reset progress
        uploadProgress[roomType] = 0;
        updateProgress(roomType, 0);
        
        // Simulate upload progress
        const interval = setInterval(() => {
            uploadProgress[roomType] += Math.floor(Math.random() * 10) + 5;
            
            if (uploadProgress[roomType] >= 100) {
                uploadProgress[roomType] = 100;
                clearInterval(interval);
                
                // Show success message
                showAlert(`Successfully uploaded ${uploadedFiles[roomType].length} ${uploadedFiles[roomType].length === 1 ? 'file' : 'files'} for ${roomType}.`, 'success');
            }
            
            updateProgress(roomType, uploadProgress[roomType]);
        }, 200);
    }
    
    function updateProgress(roomType, percent) {
        const progressBar = document.querySelector(`#${roomType}Upload .progress-bar`);
        const progressText = document.querySelector(`#${roomType}Upload .progress-text`);
        
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressText.textContent = `${percent}%`;
        
        // Update progress bar color based on percentage
        if (percent < 30) {
            progressBar.classList.remove('bg-success', 'bg-warning');
            progressBar.classList.add('bg-primary');
        } else if (percent < 70) {
            progressBar.classList.remove('bg-primary', 'bg-success');
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.remove('bg-primary', 'bg-warning');
            progressBar.classList.add('bg-success');
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function showAlert(message, type) {
        // Remove any existing alerts
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // Create alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.role = 'alert';
        alertDiv.style.zIndex = '1100';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to page
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
    
    // Initialize the first room as active
    if (roomTabs.length > 0) {
        roomTabs[0].click();
    }
});
