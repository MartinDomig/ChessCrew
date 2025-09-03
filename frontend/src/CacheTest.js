import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Paper,
  Alert
} from '@mui/material';
import { getCacheInfo, clearApiCache } from './api';

const CacheTest = () => {
  const [cacheInfo, setCacheInfo] = useState({ totalEntries: 0, entries: [] });
  const [message, setMessage] = useState('');

  const loadCacheInfo = async () => {
    try {
      const info = await getCacheInfo();
      setCacheInfo(info);
      setMessage(`Cache has ${info.totalEntries} entries`);
    } catch (error) {
      setMessage('Failed to load cache info');
      console.error(error);
    }
  };

  const clearCache = async () => {
    try {
      await clearApiCache();
      setMessage('Cache cleared successfully');
      await loadCacheInfo();
    } catch (error) {
      setMessage('Failed to clear cache');
      console.error(error);
    }
  };

  useEffect(() => {
    loadCacheInfo();
  }, []);

  return (
    <Paper elevation={1} sx={{ p: 2, m: 2 }}>
      <Typography variant="h6" gutterBottom>
        Cache Test
      </Typography>
      
      {message && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2">
          Total cached entries: {cacheInfo.totalEntries}
        </Typography>
      </Box>
      
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button variant="outlined" onClick={loadCacheInfo}>
          Refresh Info
        </Button>
        <Button variant="outlined" color="error" onClick={clearCache}>
          Clear Cache
        </Button>
      </Box>
      
      {cacheInfo.entries.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2">Cached URLs:</Typography>
          {cacheInfo.entries.slice(0, 5).map((entry, index) => (
            <Typography key={index} variant="body2" sx={{ fontSize: '0.8rem' }}>
              {entry.url}
            </Typography>
          ))}
          {cacheInfo.entries.length > 5 && (
            <Typography variant="body2" color="text.secondary">
              ... and {cacheInfo.entries.length - 5} more
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default CacheTest;
