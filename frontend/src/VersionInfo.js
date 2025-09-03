import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Box, Typography, Chip } from '@mui/material';

export const VersionInfo = forwardRef(({ compact = false }, ref) => {
  const [version, setVersion] = useState('');
  const [buildTime, setBuildTime] = useState('');

  const fetchVersion = () => {
    // Try to get version from service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then((registration) => {
        if (registration && registration.active) {
          // Extract version from service worker script with cache busting
          fetch(`/sw.js?t=${Date.now()}`)
            .then(response => response.text())
            .then(text => {
              const versionMatch = text.match(/CACHE_VERSION = '([^']+)'/);
              if (versionMatch) {
                const cacheVersion = versionMatch[1];
                setVersion(cacheVersion);
                
                // Extract timestamp from version (format: vXXXXXXXXXXXXX)
                const timestamp = cacheVersion.replace('v', '');
                if (timestamp && !isNaN(timestamp)) {
                  const buildDate = new Date(parseInt(timestamp));
                  setBuildTime(buildDate.toLocaleString('de-DE'));
                }
              }
            })
            .catch(() => {
              setVersion('unknown');
            });
        }
      });
    } else {
      setVersion('no-sw');
    }
  };

  useEffect(() => {
    fetchVersion();
  }, []);

  useImperativeHandle(ref, () => ({
    refresh: fetchVersion
  }), []);

  if (!version) return null;

  if (compact) {
    return (
      <Chip 
        label={`v${version.replace('v', '').slice(-8)}`} 
        size="small" 
        variant="outlined"
        title={`Version: ${version}${buildTime ? ` (${buildTime})` : ''}`}
      />
    );
  }

  return (
    <Box sx={{ p: 2, borderTop: '1px solid #eee', backgroundColor: '#fafafa' }}>
      <Typography variant="caption" color="text.secondary">
        Version: {version}
      </Typography>
      {buildTime && (
        <Typography variant="caption" color="text.secondary" display="block">
          Erstellt: {buildTime}
        </Typography>
      )}
    </Box>
  );
});
