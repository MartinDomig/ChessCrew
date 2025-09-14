import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { ImportExport, Link } from '@mui/icons-material';
import { apiFetch } from './api';

export default function TournamentImportDialog({ open, onClose, onImported }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

  const handleClose = () => {
    setUrl('');
    setError('');
    setImportResult(null);
    onClose();
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
    setError('');
  };

  const handleImport = async () => {
    if (!url.trim()) {
      setError('Bitte geben Sie eine Turnier-URL ein.');
      return;
    }

    setImporting(true);
    setError('');

    try {
      const result = await apiFetch('/tournaments/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() })
      });

      setImportResult(result);
      if (result.success && onImported) {
        onImported();
      }
    } catch (err) {
      setError(err.message || 'Import fehlgeschlagen.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <Dialog open={open && !importResult} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ImportExport />
          Turnier importieren
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Fügen Sie die URL eines Turniers von chess-results.com ein, um es zu importieren.
            </Typography>
            <TextField
              fullWidth
              label="Turnier-URL"
              placeholder="https://chess-results.com/tnr123456.aspx"
              value={url}
              onChange={handleUrlChange}
              disabled={importing}
              InputProps={{
                startAdornment: <Link sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={importing}>
            Abbrechen
          </Button>
          <Button
            onClick={handleImport}
            variant="contained"
            disabled={importing || !url.trim()}
            startIcon={importing ? <CircularProgress size={20} /> : <ImportExport />}
          >
            {importing ? 'Importiere...' : 'Importieren'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Result Dialog */}
      <Dialog open={!!importResult} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {importResult?.success ? 'Import erfolgreich' : 'Import fehlgeschlagen'}
        </DialogTitle>
        <DialogContent>
          <Alert severity={importResult?.success ? 'success' : 'error'} sx={{ mt: 1 }}>
            {importResult?.message}
          </Alert>
          {importResult?.success && importResult?.tournament_id && (
            <Typography variant="body2" sx={{ mt: 2 }}>
              Turnier-ID: {importResult.tournament_id}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} variant="contained">
            Schließen
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
