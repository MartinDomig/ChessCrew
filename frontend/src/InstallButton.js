import React, { useState, useEffect } from 'react';
import { Button, Fab } from '@mui/material';
import { GetApp as InstallIcon } from '@mui/icons-material';
import { installPWA, isAppInstalled } from './pwaUtils';

const InstallButton = ({ variant = 'fab', sx = {} }) => {
  const [showInstall, setShowInstall] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  useEffect(() => {
    // Check if app is already installed
    if (isAppInstalled()) {
      return;
    }

    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    const handleAppInstalled = () => {
      setShowInstall(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    const result = await installPWA();
    if (result) {
      setShowInstall(false);
    }
  };

  if (!showInstall) {
    return null;
  }

  const defaultSx = {
    position: 'fixed',
    bottom: 16,
    right: 16,
    zIndex: 1000,
    ...sx
  };

  if (variant === 'fab') {
    return (
      <Fab
        color="primary"
        aria-label="install app"
        onClick={handleInstallClick}
        sx={defaultSx}
      >
        <InstallIcon />
      </Fab>
    );
  }

  return (
    <Button
      variant="contained"
      startIcon={<InstallIcon />}
      onClick={handleInstallClick}
      sx={defaultSx}
    >
      Install App
    </Button>
  );
};

export default InstallButton;
