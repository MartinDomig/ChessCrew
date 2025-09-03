import React from 'react';
import { 
  Chip, 
  Tooltip, 
  Box 
} from '@mui/material';
import { 
  Schedule as StaleIcon,
  CloudOff as OfflineIcon 
} from '@mui/icons-material';

/**
 * Component to show when data is stale (cached but older than normal expiry)
 * Usage: <StaleDataIndicator data={apiResponse} />
 */
const StaleDataIndicator = ({ data, sx = {} }) => {
  // Check if data has stale indicators
  if (!data || !data._isStale || !data._cacheAge) {
    return null;
  }

  const ageMinutes = Math.floor(data._cacheAge / 60000);
  const ageHours = Math.floor(ageMinutes / 60);
  
  let ageText;
  if (ageHours > 0) {
    ageText = `${ageHours}h ${ageMinutes % 60}m old`;
  } else {
    ageText = `${ageMinutes}m old`;
  }

  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', ...sx }}>
      <Tooltip 
        title={`This data is from cache and may be outdated. Last updated ${ageText}. Connect to internet for fresh data.`}
        arrow
      >
        <Chip
          icon={<StaleIcon />}
          label={`Cached (${ageText})`}
          size="small"
          color="warning"
          variant="outlined"
          sx={{ 
            fontSize: '0.75rem',
            height: 24
          }}
        />
      </Tooltip>
    </Box>
  );
};

/**
 * Hook to check if any data in an object or array has stale indicators
 */
export const useHasStaleData = (data) => {
  if (!data) return false;
  
  // Check if single object has stale data
  if (data._isStale) return true;
  
  // Check if array contains any stale data
  if (Array.isArray(data)) {
    return data.some(item => item && item._isStale);
  }
  
  // Check if object properties contain stale data
  if (typeof data === 'object') {
    return Object.values(data).some(value => 
      value && typeof value === 'object' && value._isStale
    );
  }
  
  return false;
};

/**
 * Component to show a global offline/stale data banner
 */
export const StaleDataBanner = ({ data }) => {
  const hasStaleData = useHasStaleData(data);
  
  if (!hasStaleData || navigator.onLine) {
    return null;
  }

  return (
    <Box 
      sx={{ 
        bgcolor: 'warning.light', 
        color: 'warning.contrastText',
        px: 2, 
        py: 1,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        borderRadius: 1,
        mb: 1
      }}
    >
      <OfflineIcon fontSize="small" />
      <span style={{ fontSize: '0.875rem' }}>
        You're offline. Some data may be outdated.
      </span>
    </Box>
  );
};

export default StaleDataIndicator;
