import React, { useState, useEffect } from 'react';
import { 
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box
} from '@mui/material';
import { 
  GetApp as InstallIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const InstallPWA = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      console.log('PWA install prompt available');
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      console.log('PWA was installed');
      setIsInstallable(false);
      setDeferredPrompt(null);
      setShowInstallDialog(false);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = () => {
    setShowInstallDialog(true);
  };

  const handleInstallConfirm = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
      setIsInstallable(false);
    } else {
      console.log('User dismissed the install prompt');
    }
    
    setDeferredPrompt(null);
    setShowInstallDialog(false);
  };

  const handleInstallCancel = () => {
    setShowInstallDialog(false);
  };

  // Don't show if already installed or not installable
  if (!isInstallable) {
    return null;
  }

  return (
    <>
      <Fab
        color="primary"
        aria-label="install app"
        onClick={handleInstallClick}
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1000,
        }}
      >
        <InstallIcon />
      </Fab>

      <Dialog
        open={showInstallDialog}
        onClose={handleInstallCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Install ChessCrew App
        </DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body1" gutterBottom>
              Install ChessCrew as a Progressive Web App for:
            </Typography>
            <Box sx={{ mt: 2, textAlign: 'left' }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✅ Faster loading times
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✅ Offline access to your data
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✅ Full-screen app experience
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✅ Add to your device's home screen
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleInstallCancel} startIcon={<CloseIcon />}>
            Not Now
          </Button>
          <Button 
            onClick={handleInstallConfirm} 
            variant="contained" 
            startIcon={<InstallIcon />}
          >
            Install App
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default InstallPWA;
