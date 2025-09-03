// PWA utilities for managing install prompts and offline status

let deferredPrompt;
let isInstalled = false;

// Check if the app is installed
export const isAppInstalled = () => {
  return window.matchMedia && window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone ||
         document.referrer.includes('android-app://');
};

// Initialize PWA features
export const initializePWA = () => {
  isInstalled = isAppInstalled();
  
  // Listen for the beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('PWA install prompt available');
    e.preventDefault();
    deferredPrompt = e;
    
    // You can show a custom install button here
    showInstallButton();
  });

  // Listen for app installed event
  window.addEventListener('appinstalled', (e) => {
    console.log('PWA was installed');
    isInstalled = true;
    hideInstallButton();
  });

  // Listen for online/offline events
  window.addEventListener('online', () => {
    console.log('App is back online');
    showOnlineStatus();
  });

  window.addEventListener('offline', () => {
    console.log('App is offline');
    showOfflineStatus();
  });
};

// Show install button
const showInstallButton = () => {
  // You can implement a custom install button UI here
  console.log('Install button should be shown');
};

// Hide install button
const hideInstallButton = () => {
  // Hide the install button
  console.log('Install button should be hidden');
};

// Trigger the install prompt
export const installPWA = async () => {
  if (!deferredPrompt) {
    console.log('Install prompt not available');
    return false;
  }

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  
  if (outcome === 'accepted') {
    console.log('User accepted the install prompt');
  } else {
    console.log('User dismissed the install prompt');
  }
  
  deferredPrompt = null;
  return outcome === 'accepted';
};

// Show online status
const showOnlineStatus = () => {
  // Remove any offline indicators
  document.body.classList.remove('offline');
  document.body.classList.add('online');
};

// Show offline status
const showOfflineStatus = () => {
  // Add offline indicators
  document.body.classList.remove('online');
  document.body.classList.add('offline');
};

// Check if the user is online
export const isOnline = () => {
  return navigator.onLine;
};

// Register for background sync
export const registerBackgroundSync = async (tag) => {
  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    const registration = await navigator.serviceWorker.ready;
    return registration.sync.register(tag);
  }
  return Promise.reject('Background sync not supported');
};

// Request notification permission
export const requestNotificationPermission = async () => {
  if ('Notification' in window) {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  return false;
};

// Update service worker
export const updateServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready;
    return registration.update();
  }
};

// Check for service worker updates
export const checkForUpdates = () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      // The service worker has been updated, reload the page
      window.location.reload();
    });
  }
};
