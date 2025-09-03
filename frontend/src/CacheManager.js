import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Chip, 
  List, 
  ListItem, 
  ListItemText, 
  Divider,
  Alert,
  Paper,
  Grid,
  IconButton,
  Collapse
} from '@mui/material';
import { 
  Refresh as RefreshIcon, 
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CloudOff as OfflineIcon,
  Cloud as OnlineIcon,
  Storage as CacheIcon
} from '@mui/icons-material';
import { clearApiCache, getCacheInfo } from './api';

const CacheManager = () => {
  const [cacheInfo, setCacheInfo] = useState({ totalEntries: 0, entries: [] });
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadCacheInfo = async () => {
    setLoading(true);
    try {
      const info = await getCacheInfo();
      setCacheInfo(info);
    } catch (error) {
      console.error('Failed to load cache info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await clearApiCache();
      await loadCacheInfo();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  const formatAge = (ageMs) => {
    const minutes = Math.floor(ageMs / 60000);
    const seconds = Math.floor((ageMs % 60000) / 1000);
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const formatUrl = (url) => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname + urlObj.search;
    } catch {
      return url;
    }
  };

  useEffect(() => {
    loadCacheInfo();

    const handleOnlineStatus = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOnlineStatus);

    return () => {
      window.removeEventListener('online', handleOnlineStatus);
      window.removeEventListener('offline', handleOnlineStatus);
    };
  }, []);

  const validEntries = cacheInfo.entries.filter(entry => !entry.expired);
  const expiredEntries = cacheInfo.entries.filter(entry => entry.expired);

  return (
    <Paper elevation={1} sx={{ p: 2, m: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={1}>
          <CacheIcon />
          <Typography variant="h6">Cache Manager</Typography>
          {isOnline ? (
            <Chip icon={<OnlineIcon />} label="Online" color="success" size="small" />
          ) : (
            <Chip icon={<OfflineIcon />} label="Offline" color="warning" size="small" />
          )}
        </Box>
        <IconButton onClick={() => setExpanded(!expanded)}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      <Grid container spacing={2} mb={2}>
        <Grid item xs={6} sm={3}>
          <Chip 
            label={`${validEntries.length} cached`} 
            color="primary" 
            variant="outlined" 
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <Chip 
            label={`${expiredEntries.length} expired`} 
            color="warning" 
            variant="outlined" 
          />
        </Grid>
      </Grid>

      <Box display="flex" gap={1} mb={2}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadCacheInfo}
          disabled={loading}
          size="small"
        >
          Refresh
        </Button>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={handleClearCache}
          size="small"
        >
          Clear Cache
        </Button>
      </Box>

      <Collapse in={expanded}>
        {!isOnline && (
          <Alert severity="info" sx={{ mb: 2 }}>
            You're offline. The app will use cached data for GET requests and prevent write operations.
          </Alert>
        )}

        {validEntries.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Valid Cache Entries ({validEntries.length})
            </Typography>
            <List dense>
              {validEntries.map((entry, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={formatUrl(entry.url)}
                    secondary={`Cached ${formatAge(entry.age)} ago`}
                  />
                  <Chip
                    label="Valid"
                    color="success"
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {expiredEntries.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Expired Cache Entries ({expiredEntries.length})
            </Typography>
            <List dense>
              {expiredEntries.map((entry, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={formatUrl(entry.url)}
                    secondary={`Expired ${formatAge(entry.age - 300000)} ago`}
                  />
                  <Chip
                    label="Expired"
                    color="warning"
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {cacheInfo.entries.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No cached API requests yet. Make some GET requests to see them here.
          </Typography>
        )}
      </Collapse>
    </Paper>
  );
};

export default CacheManager;
