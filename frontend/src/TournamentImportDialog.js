import ImportExportIcon from '@mui/icons-material/ImportExport';
import {Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography} from '@mui/material';
import React, {useState} from 'react';

import {apiFetch} from './api';

export default function TournamentImportDialog({open, onClose, onImported}) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');

  const handleClose = () => {
    setFile(null);
    setError('');
    setImportResult(null);
    onClose();
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Bitte wählen Sie eine XLSX-Datei aus.');
      return;
    }
    if (!date) {
      setError('Bitte geben Sie ein Turnierdatum an.');
      return;
    }
    if (!location) {
      setError('Bitte geben Sie einen Turnierort an.');
      return;
    }
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('date', date);
    formData.append('location', location);
    try {
      const result = await apiFetch(
          '/tournaments-import-xlsx', {method: 'POST', body: formData});
      setImportResult(result.imported);
      if (onImported) onImported();
    } catch (err) {
      setError('Upload fehlgeschlagen.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <Dialog open={open && !importResult} onClose={handleClose}>
        <DialogTitle>Import Turnierergebnisse</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              component="label"
              startIcon={<ImportExportIcon />}
              sx={{ mb: 2 }}
            >
              Datei auswählen
              <input
                type='file'
                accept='.xlsx'
                hidden
                onChange={handleFileChange}
              />
            </Button>
            {file && (
              <Typography
                variant='body2'
                sx={{
                  maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap', display: 'block'
                }}
              >
                {file.name}
              </Typography>
            )}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                id="tournament-date"
                label="Turnierdatum"
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                slotProps={{
                  inputLabel: {
                    shrink: true,
                  },
                }}
                fullWidth
                sx={{ mb: 2 }}
              />
              <TextField
                id='tournament-location'
                label='Turnierort'
                type='text'
                value={location}
                onChange={e => setLocation(e.target.value)}
                placeholder='Ort des Turniers'
                fullWidth
              />
            </Box>
            {error && <Typography color="error">{error}</Typography>}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={uploading}>Abbrechen</Button>
          <Button onClick={handleUpload} disabled={uploading || !file} variant="contained" color="primary">
            {uploading ? 'Importiere...' : 'Importieren'}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={!!importResult} onClose={handleClose}>
        <DialogTitle>Import abgeschlossen</DialogTitle>
        <DialogContent>
          <Typography>
            {importResult === 1
              ? '1 Spiel wurde importiert.'
              : `${importResult} Spiele wurden importiert.`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} autoFocus variant="contained">OK</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
