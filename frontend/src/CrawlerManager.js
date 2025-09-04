import React, { useState } from 'react';
import { Card, CardContent, Typography, Button, Box, Alert, CircularProgress, Chip } from '@mui/material';
import { Download, PlayArrow, Refresh, Schedule } from '@mui/icons-material';

const CrawlerManager = () => {
  const [crawlerStatus, setCrawlerStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchCrawlerStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/crawler/status');
      if (response.ok) {
        const data = await response.json();
        setCrawlerStatus(data);
      } else {
        console.error('Failed to fetch crawler status');
      }
    } catch (error) {
      console.error('Error fetching crawler status:', error);
    } finally {
      setLoading(false);
    }
  };

  const runCrawler = async () => {
    try {
      setIsRunning(true);
      setLastResult(null);
      
      const response = await fetch('/api/crawler/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setLastResult({
          success: true,
          message: data.message,
          processedCount: data.processed_count
        });
      } else {
        setLastResult({
          success: false,
          message: data.message
        });
      }
      
      // Refresh status after run
      setTimeout(fetchCrawlerStatus, 1000);
      
    } catch (error) {
      setLastResult({
        success: false,
        message: `Error: ${error.message}`
      });
    } finally {
      setIsRunning(false);
    }
  };

  React.useEffect(() => {
    fetchCrawlerStatus();
  }, []);

  const formatLogLines = (logs) => {
    if (!logs || !Array.isArray(logs)) return [];
    return logs.slice(-10).map((line, index) => (
      <Typography key={index} variant="caption" display="block" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
        {line}
      </Typography>
    ));
  };

  return (
    <Card sx={{ maxWidth: 800, margin: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h5" component="h2" gutterBottom>
            <Download sx={{ mr: 1, verticalAlign: 'middle' }} />
            Chess Results Crawler
          </Typography>
          <Button 
            variant="outlined" 
            onClick={fetchCrawlerStatus}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
          >
            Refresh Status
          </Button>
        </Box>

        <Typography variant="body2" color="textSecondary" paragraph>
          Automatically import finished Austrian tournaments from chess-results.com with ELO calculation.
        </Typography>

        {/* Crawler Controls */}
        <Box mb={3}>
          <Button
            variant="contained"
            onClick={runCrawler}
            disabled={isRunning}
            startIcon={isRunning ? <CircularProgress size={16} /> : <PlayArrow />}
            sx={{ mr: 2 }}
          >
            {isRunning ? 'Running Crawler...' : 'Run Crawler Now'}
          </Button>
        </Box>

        {/* Last Run Result */}
        {lastResult && (
          <Alert 
            severity={lastResult.success ? 'success' : 'error'} 
            sx={{ mb: 2 }}
          >
            {lastResult.message}
            {lastResult.processedCount !== undefined && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Processed {lastResult.processedCount} tournaments
              </Typography>
            )}
          </Alert>
        )}

        {/* Status Information */}
        {crawlerStatus && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Status Information
            </Typography>
            
            <Box display="flex" gap={1} mb={2} flexWrap="wrap">
              <Chip 
                icon={<Schedule />}
                label={`Last Run: ${crawlerStatus.last_run || 'Never'}`}
                color={crawlerStatus.last_run ? 'success' : 'default'}
                variant="outlined"
                size="small"
              />
              <Chip 
                label={`Imported: ${crawlerStatus.imported_tournaments || 0} tournaments`}
                color="info"
                variant="outlined"
                size="small"
              />
              <Chip 
                label={crawlerStatus.log_file_exists ? 'Logs Available' : 'No Logs'}
                color={crawlerStatus.log_file_exists ? 'success' : 'warning'}
                variant="outlined"
                size="small"
              />
            </Box>

            {/* Recent Logs */}
            {crawlerStatus.recent_logs && crawlerStatus.recent_logs.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Recent Log Entries:
                </Typography>
                <Box 
                  sx={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: 1, 
                    borderRadius: 1,
                    maxHeight: 200,
                    overflow: 'auto'
                  }}
                >
                  {formatLogLines(crawlerStatus.recent_logs)}
                </Box>
              </Box>
            )}
          </Box>
        )}

        {/* Setup Instructions */}
        <Box mt={3}>
          <Typography variant="h6" gutterBottom>
            Automatic Schedule Setup
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            To run the crawler automatically every day, add this cron job:
          </Typography>
          <Box 
            sx={{ 
              backgroundColor: '#f5f5f5', 
              padding: 2, 
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem'
            }}
          >
            <Typography component="pre">
              {`# Run chess results crawler daily at 2 AM
0 2 * * * /home/martin/chesscrew/backend/run_crawler_cron.sh`}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CrawlerManager;
