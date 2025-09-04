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
                
                // Parse version with build time: "v1.0.0-8-g47243d9 (2025-09-04T22:30:00.000Z)"
                const timeMatch = cacheVersion.match(/(.+?)\s*\(([^)]+)\)/);
                if (timeMatch) {
                  const gitVersion = timeMatch[1].trim();
                  const buildTimestamp = timeMatch[2].trim();
                  
                  // Format the build time nicely using browser locale
                  try {
                    const buildDate = new Date(buildTimestamp);
                    const userLocale = navigator.language || navigator.languages?.[0] || 'en-US';
                    const formattedTime = buildDate.toLocaleString(userLocale, {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    });
                    setBuildTime(`${gitVersion} (${formattedTime})`);
                  } catch (e) {
                    setBuildTime(gitVersion);
                  }
                } else {
                  // Fallback for old format without timestamp
                  setBuildTime(cacheVersion);
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
