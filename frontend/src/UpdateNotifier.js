import React, { useState, useEffect } from 'react';
import { Button, Snackbar, Alert } from '@mui/material';

export function UpdateNotifier() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [registration, setRegistration] = useState(null);

  useEffect(() => {
    // Check if service worker is supported
    if ('serviceWorker' in navigator) {
      // Listen for service worker updates
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // Reload the page when a new service worker takes control
        window.location.reload();
      });

      // Check for updates
      navigator.serviceWorker.getRegistration().then((reg) => {
        if (reg) {
          setRegistration(reg);
          
          // Listen for waiting service worker
          if (reg.waiting) {
            setUpdateAvailable(true);
          }

          // Listen for new service worker installing
          reg.addEventListener('updatefound', () => {
            const newWorker = reg.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  setUpdateAvailable(true);
                }
              });
            }
          });
        }
      });

      // Check for updates periodically (every 5 minutes)
      const checkForUpdates = () => {
        navigator.serviceWorker.getRegistration().then((reg) => {
          if (reg) {
            reg.update();
          }
        });
      };

      const updateInterval = setInterval(checkForUpdates, 5 * 60 * 1000); // 5 minutes
      
      return () => clearInterval(updateInterval);
    }
  }, []);

  const handleUpdate = () => {
    if (registration && registration.waiting) {
      // Tell the waiting service worker to skip waiting and become active
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    } else {
      // Fallback: just reload the page
      window.location.reload();
    }
  };

  const handleDismiss = () => {
    setUpdateAvailable(false);
  };

  return (
    <Snackbar
      open={updateAvailable}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      sx={{ mb: 2 }}
    >
      <Alert 
        severity="info" 
        action={
          <>
            <Button color="inherit" size="small" onClick={handleUpdate}>
              Aktualisieren
            </Button>
            <Button color="inherit" size="small" onClick={handleDismiss}>
              Später
            </Button>
          </>
        }
      >
        Eine neue Version ist verfügbar!
      </Alert>
    </Snackbar>
  );
}
