import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, Typography } from '@mui/material';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import { apiFetch } from './api';

export default function TournamentImportDialog({ open, onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState(null);

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
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const result = await apiFetch('/tournaments-import-xlsx', {
        method: 'POST',
        body: formData
      });
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
        <DialogTitle>Import Meldekartei</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              component="label"
              startIcon={<ImportExportIcon />}
              sx={{ mb: 2 }}
            >
              Datei auswählen
              <input
                type="file"
                accept=".xlsx"
                hidden
                onChange={handleFileChange}
              />
            </Button>
            {file && (
              <Typography
                variant="body2"
                sx={{
                  maxWidth: 250,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  display: 'block'
                }}
              >
                {file.name}
              </Typography>
            )}
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
