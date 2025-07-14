// Offline Manager for AXA App
// Handles service worker registration, online/offline detection, and offline data management

class OfflineManager {
  constructor() {
    this.registration = null;
    this.isOnline = navigator.onLine;
    this.offlineQueue = [];
    this.init();
  }

  async init() {
    this.setupEventListeners();
    await this.registerServiceWorker();
    this.setupOfflineUI();
    this.setupBackgroundSync();
    this.updateOnlineStatus();
  }

  setupEventListeners() {
    // Listen for online/offline status changes
    window.addEventListener('online', this.handleOnlineStatusChange.bind(this));
    window.addEventListener('offline', this.handleOnlineStatusChange.bind(this));
    
    // Listen for messages from service worker
    navigator.serviceWorker?.addEventListener('message', this.handleServiceWorkerMessage.bind(this));
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.registration = await navigator.serviceWorker.register('/static/service-worker.js');
        console.log('ServiceWorker registration successful');
        
        // Check for updates
        if (this.registration.waiting) {
          this.onNewServiceWorker(this.registration.waiting);
        }
        
        this.registration.addEventListener('updatefound', () => {
          const newWorker = this.registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              this.onNewServiceWorker(newWorker);
            }
          });
        });
        
      } catch (error) {
        console.error('ServiceWorker registration failed:', error);
      }
    }
  }

  onNewServiceWorker(worker) {
    // Notify user about the update
    if (confirm('A new version of the app is available. Reload to update?')) {
      worker.postMessage({ action: 'skipWaiting' });
    }
  }

  handleServiceWorkerMessage(event) {
    const { action } = event.data;
    
    switch (action) {
      case 'reload':
        window.location.reload();
        break;
      case 'offline':
        this.showOfflineNotification();
        break;
      // Add more message handlers as needed
    }
  }

  setupOfflineUI() {
    // Create offline status indicator
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'offline-status';
    statusIndicator.style.position = 'fixed';
    statusIndicator.style.bottom = '20px';
    statusIndicator.style.right = '20px';
    statusIndicator.style.padding = '10px 15px';
    statusIndicator.style.borderRadius = '20px';
    statusIndicator.style.color = 'white';
    statusIndicator.style.fontWeight = 'bold';
    statusIndicator.style.zIndex = '1000';
    statusIndicator.style.display = 'none';
    statusIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    
    document.body.appendChild(statusIndicator);
    this.updateOnlineStatus();
  }

  updateOnlineStatus() {
    const statusIndicator = document.getElementById('offline-status');
    if (!statusIndicator) return;
    
    this.isOnline = navigator.onLine;
    
    if (this.isOnline) {
      statusIndicator.textContent = 'Online';
      statusIndicator.style.backgroundColor = '#4CAF50';
      statusIndicator.style.display = 'block';
      
      // Hide after 3 seconds
      setTimeout(() => {
        statusIndicator.style.display = 'none';
      }, 3000);
      
      // Process any queued requests
      this.processQueue();
    } else {
      statusIndicator.textContent = 'Offline - Working in offline mode';
      statusIndicator.style.backgroundColor = '#f44336';
      statusIndicator.style.display = 'block';
    }
  }

  handleOnlineStatusChange() {
    this.updateOnlineStatus();
  }

  showOfflineNotification() {
    const notification = document.createElement('div');
    notification.textContent = 'You are currently offline. Some features may be limited.';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.backgroundColor = '#f44336';
    notification.style.color = 'white';
    notification.style.padding = '15px 25px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '1000';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 1s';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 1000);
    }, 5000);
  }

  async setupBackgroundSync() {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      try {
        await navigator.serviceWorker.ready;
        const registration = await navigator.serviceWorker.registration;
        
        // Register for background sync
        await registration.sync.register('sync-requests');
        console.log('Background sync registered');
      } catch (error) {
        console.error('Background sync registration failed:', error);
      }
    }
  }

  async addToQueue(request) {
    if (!this.isOnline) {
      // Store the request for later processing
      const db = await this.openDatabase();
      const tx = db.transaction(['pendingRequests'], 'readwrite');
      const store = tx.objectStore('pendingRequests');
      
      await store.add({
        url: request.url,
        method: request.method,
        headers: Object.fromEntries(request.headers.entries()),
        body: request.method !== 'GET' && request.method !== 'HEAD' 
          ? await request.clone().text() 
          : null,
        timestamp: new Date().getTime()
      });
      
      // Notify user
      this.showOfflineNotification();
      
      // Return a response that indicates the request was queued
      return new Response(JSON.stringify({
        success: false,
        message: 'Request queued for when you are back online',
        queued: true
      }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // If online, just proceed with the request
    return fetch(request);
  }

  async processQueue() {
    if (!this.isOnline) return;
    
    const db = await this.openDatabase();
    const tx = db.transaction(['pendingRequests'], 'readwrite');
    const store = tx.objectStore('pendingRequests');
    const requests = await store.getAll();
    
    for (const request of requests) {
      try {
        const { url, method, headers, body } = request;
        const response = await fetch(url, {
          method,
          headers: new Headers(headers),
          body: body ? body : null
        });
        
        if (response.ok) {
          // Request succeeded, remove from queue
          await store.delete(request.id);
        }
      } catch (error) {
        console.error('Failed to process queued request:', error);
      }
    }
  }

  async openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('axa-offline-db', 1);
      
      request.onerror = (event) => {
        console.error('Database error:', event.target.error);
        reject(event.target.error);
      };
      
      request.onsuccess = (event) => {
        resolve(event.target.result);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        if (!db.objectStoreNames.contains('pendingRequests')) {
          const store = db.createObjectStore('pendingRequests', { keyPath: 'id', autoIncrement: true });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('qrData')) {
          const store = db.createObjectStore('qrData', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  // Save QR data to local storage
  async saveQRData(qrData) {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(['qrData'], 'readwrite');
      const store = tx.objectStore('qrData');
      
      await store.put({
        id: qrData.id || Date.now().toString(),
        data: qrData,
        timestamp: new Date().getTime()
      });
      
      return true;
    } catch (error) {
      console.error('Error saving QR data:', error);
      return false;
    }
  }

  // Get all saved QR data
  async getAllQRData() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(['qrData'], 'readonly');
      const store = tx.objectStore('qrData');
      
      return new Promise((resolve) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => resolve([]);
      });
    } catch (error) {
      console.error('Error getting QR data:', error);
      return [];
    }
  }
}

// Initialize the Offline Manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize if service workers are supported
  if ('serviceWorker' in navigator) {
    window.offlineManager = new OfflineManager();
    
    // Override the fetch API to handle offline requests
    const originalFetch = window.fetch;
    window.fetch = async function(resource, options = {}) {
      // For API requests, use the offline manager
      if (typeof resource === 'string' && resource.startsWith('/api/')) {
        try {
          // First try the original fetch
          return await originalFetch(resource, options);
        } catch (error) {
          // If offline, add to queue
          if (!navigator.onLine) {
            return window.offlineManager.addToQueue(new Request(resource, options));
          }
          throw error;
        }
      }
      
      // For non-API requests, just use the original fetch
      return originalFetch(resource, options);
    };
  }
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OfflineManager;
}
