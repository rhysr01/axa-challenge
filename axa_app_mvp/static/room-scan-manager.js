// Room Scan Manager - Handles offline storage and sync for room scans
class RoomScanManager {
    constructor() {
        this.dbName = 'axa-offline-db';
        this.storeName = 'pendingRoomScans';
        this.initialized = false;
        this.init();
    }

    async init() {
        if (this.initialized) return;
        
        // Open or create the database
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 2);
            
            request.onerror = (event) => {
                console.error('Error opening database:', event.target.error);
                reject(event.target.error);
            };
            
            request.onsuccess = (event) => {
                this.db = event.target.result;
                this.initialized = true;
                console.log('RoomScanManager initialized');
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object store for pending room scans if it doesn't exist
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { 
                        keyPath: 'id',
                        autoIncrement: true 
                    });
                    
                    // Create indexes for querying
                    store.createIndex('status', 'status', { unique: false });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                    console.log('Created object store:', this.storeName);
                }
            };
        });
    }

    // Save a room scan for offline sync
    async saveRoomScan(roomScan) {
        if (!this.initialized) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            // Add timestamp and status
            roomScan.timestamp = new Date().toISOString();
            roomScan.status = 'pending';
            
            const request = store.add(roomScan);
            
            request.onsuccess = (event) => {
                console.log('Room scan saved for offline sync:', event.target.result);
                resolve(event.target.result);
                
                // Notify UI about new pending scans
                this.updatePendingScansBadge();
                
                // If online, try to sync immediately
                if (navigator.onLine) {
                    this.syncPendingScans();
                }
            };
            
            request.onerror = (event) => {
                console.error('Error saving room scan:', event.target.error);
                reject(event.target.error);
            };
        });
    }

    // Get all pending room scans
    async getPendingScans() {
        if (!this.initialized) await this.init();
        
        return new Promise((resolve) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('status');
            const request = index.getAll('pending');
            
            request.onsuccess = (event) => {
                resolve(event.target.result || []);
            };
            
            request.onerror = (event) => {
                console.error('Error getting pending scans:', event.target.error);
                resolve([]);
            };
        });
    }

    // Update a room scan status
    async updateScanStatus(id, status, response = null) {
        if (!this.initialized) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            // First get the scan
            const getRequest = store.get(id);
            
            getRequest.onsuccess = () => {
                const scan = getRequest.result;
                if (!scan) {
                    reject(new Error('Scan not found'));
                    return;
                }
                
                // Update status and response
                scan.status = status;
                if (response) {
                    scan.response = response;
                }
                
                // Save the updated scan
                const updateRequest = store.put(scan);
                
                updateRequest.onsuccess = () => {
                    console.log(`Scan ${id} updated to status: ${status}`);
                    this.updatePendingScansBadge();
                    resolve();
                };
                
                updateRequest.onerror = (event) => {
                    console.error('Error updating scan status:', event.target.error);
                    reject(event.target.error);
                };
            };
            
            getRequest.onerror = (event) => {
                console.error('Error getting scan for update:', event.target.error);
                reject(event.target.error);
            };
        });
    }

    // Delete a room scan
    async deleteScan(id) {
        if (!this.initialized) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            const request = store.delete(id);
            
            request.onsuccess = () => {
                console.log(`Scan ${id} deleted`);
                this.updatePendingScansBadge();
                resolve();
            };
            
            request.onerror = (event) => {
                console.error('Error deleting scan:', event.target.error);
                reject(event.target.error);
            };
        });
    }

    // Sync pending scans with the server
    async syncPendingScans() {
        if (!navigator.onLine) {
            console.log('Device is offline, cannot sync scans');
            return;
        }
        
        const pendingScans = await this.getPendingScans();
        
        if (pendingScans.length === 0) {
            console.log('No pending scans to sync');
            return;
        }
        
        console.log(`Syncing ${pendingScans.length} pending scans...`);
        
        // Process each pending scan
        for (const scan of pendingScans) {
            try {
                // Convert base64 image data to blob if needed
                let formData = new FormData();
                
                if (scan.scanData && scan.scanData.startsWith('data:')) {
                    // Convert base64 to blob
                    const blob = await (await fetch(scan.scanData)).blob();
                    formData.append('scanFile', blob, scan.fileName || 'scan.jpg');
                } else if (scan.scanData) {
                    // Already a file, just append
                    formData.append('scanFile', scan.scanData);
                }
                
                if (scan.notes) {
                    formData.append('notes', scan.notes);
                }
                
                // Add any additional data
                if (scan.additionalData) {
                    Object.entries(scan.additionalData).forEach(([key, value]) => {
                        formData.append(key, value);
                    });
                }
                
                // Send to server
                const response = await fetch('/api/room-scan', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Scan uploaded successfully:', result);
                    
                    // Mark as synced
                    await this.updateScanStatus(scan.id, 'synced', result);
                    
                    // Optionally delete the synced scan
                    await this.deleteScan(scan.id);
                } else {
                    throw new Error(`Server returned ${response.status}`);
                }
            } catch (error) {
                console.error('Error syncing scan:', error);
                
                // Mark as error (with retry logic)
                await this.updateScanStatus(scan.id, 'error', {
                    error: error.message,
                    retryCount: (scan.retryCount || 0) + 1,
                    lastAttempt: new Date().toISOString()
                });
            }
        }
    }

    // Update the UI to show number of pending scans
    async updatePendingScansBadge() {
        if (!this.initialized) await this.init();
        
        const pendingScans = await this.getPendingScans();
        const badge = document.getElementById('pendingScansBadge');
        
        if (badge) {
            if (pendingScans.length > 0) {
                badge.textContent = pendingScans.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
}

// Initialize the room scan manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if IndexedDB is supported
    if (!('indexedDB' in window)) {
        console.warn('IndexedDB not supported, offline functionality will be limited');
        return;
    }
    
    // Initialize the room scan manager
    window.roomScanManager = new RoomScanManager();
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
        console.log('Device is online, syncing pending scans...');
        if (window.roomScanManager) {
            window.roomScanManager.syncPendingScans();
        }
    });
    
    // Initial sync if online
    if (navigator.onLine && window.roomScanManager) {
        setTimeout(() => {
            window.roomScanManager.syncPendingScans();
        }, 2000); // Small delay to ensure everything is loaded
    }
});
