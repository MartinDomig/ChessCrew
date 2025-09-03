import React, { useState, useEffect } from 'react';
import { 
  Alert, 
  Snackbar, 
  Chip,
  Box,
  Typography
} from '@mui/material';
import { 
  CloudOff as OfflineIcon,
  Cloud as OnlineIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon
} from '@mui/icons-material';
import { preloadCommonData } from './api';

const NetworkStatus = ({ showPersistent = false }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showOfflineAlert, setShowOfflineAlert] = useState(false);
  const [showOnlineAlert, setShowOnlineAlert] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowOnlineAlert(true);
      setShowOfflineAlert(false);
      
      // Trigger background preloading when coming back online
      preloadCommonData();
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOfflineAlert(true);
      setShowOnlineAlert(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Show initial offline state if already offline
    if (!navigator.onLine) {
      setShowOfflineAlert(true);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Persistent indicator (always visible)
  if (showPersistent) {
    return (
      <Chip
        icon={isOnline ? <OnlineIcon /> : <OfflineIcon />}
        label={isOnline ? 'Online' : 'Offline'}
        color={isOnline ? 'success' : 'warning'}
        size="small"
        variant="outlined"
      />
    );
  }

  return (
    <>
      {/* Offline Alert */}
      <Snackbar
        open={showOfflineAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{ mt: 2 }}
      >
        <Alert 
          severity="warning" 
          icon={<WifiOffIcon />}
          sx={{ width: '100%' }}
          onClose={() => setShowOfflineAlert(false)}
        >
          <Box>
            <Typography variant="body2" fontWeight="bold">
              You're offline
            </Typography>
            <Typography variant="caption" display="block">
              You can browse cached content, but changes won't be saved until you're back online.
            </Typography>
          </Box>
        </Alert>
      </Snackbar>

      {/* Back Online Alert */}
      <Snackbar
        open={showOnlineAlert}
        autoHideDuration={4000}
        onClose={() => setShowOnlineAlert(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{ mt: 2 }}
      >
        <Alert 
          severity="success" 
          icon={<WifiIcon />}
          sx={{ width: '100%' }}
        >
          <Typography variant="body2" fontWeight="bold">
            You're back online!
          </Typography>
        </Alert>
      </Snackbar>
    </>
  );
};

export default NetworkStatus;
