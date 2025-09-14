import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
  Chip,
  IconButton,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { apiFetch } from './api';
import { getContrastColor } from './colorUtils';

export default function TagManagementModal({ open, onClose }) {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deletingTagId, setDeletingTagId] = useState(null);

  useEffect(() => {
    if (open) {
      loadTags();
    }
  }, [open]);

  const loadTags = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch('/tags');
      setTags(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Fehler beim Laden der Tags');
      console.error('Failed to load tags:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTag = async (tagId, tagName) => {
    if (!window.confirm(`Möchten Sie den Tag "${tagName}" wirklich löschen?`)) {
      return;
    }

    setDeletingTagId(tagId);
    setError(null);
    try {
      await apiFetch(`/tags/${tagId}`, { method: 'DELETE' });
      setTags(tags.filter(tag => tag.id !== tagId));
    } catch (err) {
      if (err.message && err.message.includes('zugewiesen')) {
        setError(`Tag "${tagName}" ist noch Spielern zugewiesen und kann nicht gelöscht werden.`);
      } else {
        setError('Fehler beim Löschen des Tags');
      }
      console.error('Failed to delete tag:', err);
    } finally {
      setDeletingTagId(null);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Tag-Verwaltung</DialogTitle>
      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Hier können Sie alle Tags verwalten. Klicken Sie auf das Löschen-Symbol, um einen Tag zu entfernen.
            </Typography>

            {tags.length === 0 ? (
              <Typography color="text.secondary">Keine Tags vorhanden</Typography>
            ) : (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {tags.map(tag => {
                  const bg = tag.color || '#1976d2';
                  const fg = getContrastColor(bg);
                  return (
                    <Box key={tag.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={tag.name}
                        style={{
                          backgroundColor: bg,
                          color: fg,
                          border: '1px solid rgba(0,0,0,0.2)'
                        }}
                      />
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteTag(tag.id, tag.name)}
                        disabled={deletingTagId === tag.id}
                        title={`Tag "${tag.name}" löschen`}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  );
                })}
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Schließen</Button>
      </DialogActions>
    </Dialog>
  );
}
