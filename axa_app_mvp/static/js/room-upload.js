// Room Upload JavaScript - Handles the room scan upload form with offline support

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const scanUploadForm = document.getElementById('scanUploadForm');
    const scanFileInput = document.getElementById('scanFile');
    const dropZone = document.getElementById('dropZone');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const changeFileBtn = document.getElementById('changeFile');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const successMessage = document.getElementById('successMessage');
    const uploadFormContainer = document.getElementById('uploadFormContainer');
    const uploadAnotherBtn = document.getElementById('uploadAnother');
    const offlineScansList = document.getElementById('offlineScansList');
    const pendingScansList = document.getElementById('pendingScansList');
    const pendingCount = document.getElementById('pendingCount');
    const offlineBadge = document.getElementById('offlineBadge');
    const pendingScansBadge = document.getElementById('pendingScansBadge');
    const uploadError = document.getElementById('uploadError');
    
    // Check if we're offline
    const isOffline = !navigator.onLine;
    
    // Show offline badge if offline
    if (isOffline) {
        offlineBadge.style.display = 'inline-block';
        offlineBadge.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
    }
    
    // Set up drag and drop
    if (dropZone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        dropZone.addEventListener('drop', handleDrop, false);
        
        // Click to select file
        dropZone.addEventListener('click', () => {
            scanFileInput.click();
        });
    }
    
    // Handle file selection
    if (scanFileInput) {
        scanFileInput.addEventListener('change', handleFileSelect);
    }
    
    // Change file button
    if (changeFileBtn) {
        changeFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            scanFileInput.value = '';
            fileInfo.style.display = 'none';
            scanFileInput.click();
        });
    }
    
    // Form submission
    if (scanUploadForm) {
        scanUploadForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Upload another button
    if (uploadAnotherBtn) {
        uploadAnotherBtn.addEventListener('click', resetForm);
    }
    
    // Check for pending scans on load
    if (window.roomScanManager) {
        updatePendingScansList();
        
        // Update the pending scans badge
        window.roomScanManager.updatePendingScansBadge();
    }
    
    // Listen for online/offline events
    window.addEventListener('online', handleOnlineStatusChange);
    window.addEventListener('offline', handleOnlineStatusChange);
    
    // Prevent default drag behaviors
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone
    function highlight() {
        dropZone.classList.add('dragover');
    }
    
    // Remove highlight from drop zone
    function unhighlight() {
        dropZone.classList.remove('dragover');
    }
    
    // Handle dropped files
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }
    
    // Handle file selection
    function handleFileSelect(e) {
        const files = e.target.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }
    
    // Process selected files
    function handleFiles(files) {
        const file = files[0];
        
        if (!file) return;
        
        // Check file size (max 50MB)
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            showError('File is too large. Maximum size is 50MB.');
            return;
        }
        
        // Check file type
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'video/mp4'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid file type. Please upload a JPG, PNG, or MP4 file.');
            return;
        }
        
        // Update UI
        fileName.textContent = file.name;
        fileInfo.style.display = 'block';
    }
    
    // Handle form submission
    async function handleFormSubmit(e) {
        e.preventDefault();
        
        const roomType = document.getElementById('roomType').value;
        const notes = document.getElementById('notes').value;
        const fileInput = document.getElementById('scanFile');
        
        // Validate form
        if (!roomType) {
            showError('Please select a room type.');
            return;
        }
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select a file to upload.');
            return;
        }
        
        const file = fileInput.files[0];
        
        // Check if we're offline
        if (!navigator.onLine) {
            // Save for offline upload
            await saveForOfflineUpload(roomType, file, notes);
            return;
        }
        
        // Online upload
        await uploadScan(roomType, file, notes);
    }
    
    // Upload scan to server
    async function uploadScan(roomType, file, notes) {
        const formData = new FormData();
        formData.append('roomType', roomType);
        formData.append('scanFile', file);
        if (notes) {
            formData.append('notes', notes);
        }
        
        // Show progress
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = 'Preparing upload...';
        
        // Disable form during upload
        setFormEnabled(false);
        
        try {
            // Create a new XMLHttpRequest for upload progress tracking
            const xhr = new XMLHttpRequest();
            
            // Set up progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + '%';
                    progressText.textContent = `Uploading... ${percentComplete}%`;
                }
            });
            
            // Handle response
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        // Success
                        const response = JSON.parse(xhr.responseText);
                        showSuccess(response);
                    } else {
                        // Error
                        let errorMessage = 'Upload failed. Please try again.';
                        try {
                            const errorResponse = JSON.parse(xhr.responseText);
                            if (errorResponse.detail) {
                                errorMessage = errorResponse.detail;
                            }
                        } catch (e) {
                            console.error('Error parsing error response:', e);
                        }
                        showError(errorMessage);
                        setFormEnabled(true);
                        uploadProgress.style.display = 'none';
                    }
                }
            };
            
            // Open and send the request
            xhr.open('POST', '/api/room-scan', true);
            xhr.send(formData);
            
        } catch (error) {
            console.error('Upload error:', error);
            showError('An error occurred during upload. Please try again.');
            setFormEnabled(true);
            uploadProgress.style.display = 'none';
            
            // If offline during upload, save for later
            if (!navigator.onLine) {
                await saveForOfflineUpload(roomType, file, notes);
            }
        }
    }
    
    // Save scan for offline upload
    async function saveForOfflineUpload(roomType, file, notes) {
        try {
            // Read the file as base64
            const base64Data = await readFileAsDataURL(file);
            
            // Create scan object
            const scan = {
                roomType: roomType,
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size,
                scanData: base64Data,
                notes: notes,
                timestamp: new Date().toISOString(),
                status: 'pending'
            };
            
            // Save to IndexedDB
            if (window.roomScanManager) {
                await window.roomScanManager.saveRoomScan(scan);
                
                // Show success message
                showOfflineSuccess();
                
                // Update pending scans list
                updatePendingScansList();
                
                // Reset form
                resetForm();
                
                // Show offline badge
                offlineBadge.style.display = 'inline-block';
                offlineBadge.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
            } else {
                throw new Error('Offline storage not available');
            }
        } catch (error) {
            console.error('Error saving for offline upload:', error);
            showError('Failed to save scan for offline upload. Please try again.');
        }
    }
    
    // Read file as data URL
    function readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    // Show success message
    function showSuccess(response) {
        uploadFormContainer.style.display = 'none';
        successMessage.style.display = 'block';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Show offline success message
    function showOfflineSuccess() {
        // You could show a different message for offline saves
        uploadFormContainer.style.display = 'none';
        successMessage.style.display = 'block';
        
        // Update the success message for offline
        const successTitle = successMessage.querySelector('h3');
        const successText = successMessage.querySelector('p');
        
        if (successTitle) successTitle.textContent = 'Scan Saved for Offline Upload';
        if (successText) successText.textContent = 'Your scan has been saved and will be uploaded when you are back online.';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Reset form
    function resetForm() {
        scanUploadForm.reset();
        fileInfo.style.display = 'none';
        uploadProgress.style.display = 'none';
        successMessage.style.display = 'none';
        uploadFormContainer.style.display = 'block';
        setFormEnabled(true);
        
        // Focus on the first form field
        document.getElementById('roomType').focus();
    }
    
    // Show error message
    function showError(message) {
        uploadError.textContent = message;
        uploadError.style.display = 'block';
        
        // Scroll to error
        uploadError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Hide error after 5 seconds
        setTimeout(() => {
            uploadError.style.display = 'none';
        }, 5000);
    }
    
    // Enable/disable form elements
    function setFormEnabled(enabled) {
        const formElements = scanUploadForm.elements;
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = !enabled;
        }
    }
    
    // Update pending scans list
    async function updatePendingScansList() {
        if (!window.roomScanManager) return;
        
        try {
            const pendingScans = await window.roomScanManager.getPendingScans();
            
            // Update count
            pendingCount.textContent = pendingScans.length;
            
            // Show/hide the pending scans section
            if (pendingScans.length > 0) {
                offlineScansList.style.display = 'block';
                
                // Clear current list
                pendingScansList.innerHTML = '';
                
                // Add each pending scan to the list
                pendingScans.forEach(scan => {
                    const template = document.getElementById('pendingScanTemplate').innerHTML;
                    const statusText = scan.status === 'error' ? 'Upload Failed' : 'Pending Upload';
                    
                    // Format date
                    const date = new Date(scan.timestamp);
                    const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                    
                    // Replace placeholders in template
                    const html = template
                        .replace('{{id}}', scan.id)
                        .replace('{{roomType}}', scan.roomType || 'Room Scan')
                        .replace('{{date}}', formattedDate)
                        .replace('{{status}}', scan.status)
                        .replace('{{statusText}}', statusText);
                    
                    // Create element from HTML
                    const div = document.createElement('div');
                    div.innerHTML = html.trim();
                    const scanItem = div.firstChild;
                    
                    // Add event listeners
                    const retryBtn = scanItem.querySelector('[data-action="retry"]');
                    const deleteBtn = scanItem.querySelector('[data-action="delete"]');
                    
                    if (retryBtn) {
                        retryBtn.addEventListener('click', () => retryScan(scan.id));
                    }
                    
                    if (deleteBtn) {
                        deleteBtn.addEventListener('click', () => deleteScan(scan.id));
                    }
                    
                    // Add to list
                    pendingScansList.appendChild(scanItem);
                });
            } else {
                offlineScansList.style.display = 'none';
            }
            
            // Update the pending scans badge
            if (pendingScansBadge) {
                if (pendingScans.length > 0) {
                    pendingScansBadge.textContent = pendingScans.length;
                    pendingScansBadge.style.display = 'inline-block';
                } else {
                    pendingScansBadge.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error updating pending scans list:', error);
        }
    }
    
    // Retry a failed scan upload
    async function retryScan(scanId) {
        try {
            // Get the scan data
            const scan = await window.roomScanManager.getScan(scanId);
            
            if (!scan) {
                console.error('Scan not found:', scanId);
                return;
            }
            
            // Convert base64 back to a file
            const file = await dataURLtoFile(scan.scanData, scan.fileName);
            
            // Try to upload again
            await uploadScan(scan.roomType, file, scan.notes);
            
            // If successful, remove from pending
            await window.roomScanManager.deleteScan(scanId);
            
            // Update the list
            updatePendingScansList();
            
        } catch (error) {
            console.error('Error retrying scan upload:', error);
            showError('Failed to retry upload. Please try again.');
        }
    }
    
    // Delete a pending scan
    async function deleteScan(scanId) {
        try {
            await window.roomScanManager.deleteScan(scanId);
            updatePendingScansList();
        } catch (error) {
            console.error('Error deleting scan:', error);
            showError('Failed to delete scan. Please try again.');
        }
    }
    
    // Convert data URL to file
    function dataURLtoFile(dataurl, filename) {
        const arr = dataurl.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        
        return new File([u8arr], filename, { type: mime });
    }
    
    // Handle online/offline status changes
    function handleOnlineStatusChange() {
        if (navigator.onLine) {
            // We're back online, try to sync pending scans
            if (window.roomScanManager) {
                window.roomScanManager.syncPendingScans();
                offlineBadge.style.display = 'none';
            }
        } else {
            // We're offline
            offlineBadge.style.display = 'inline-block';
            offlineBadge.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
        }
    }
});
