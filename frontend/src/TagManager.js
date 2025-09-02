import React, { useEffect, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, CircularProgress, TextField, Chip } from '@mui/material';
import { apiFetch } from './api';
import { getContrastColor } from './colorUtils';
import { SketchPicker } from 'react-color';

export default function TagManager({ player, open, onClose, onTagAdded }) {
  const [allTags, setAllTags] = useState([]);
  const [tagLoading, setTagLoading] = useState(false);
  const [tagError, setTagError] = useState(null);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#1976d2');
  const [adding, setAdding] = useState(false);
  const [showAddUI, setShowAddUI] = useState(false);

  useEffect(() => {
    if (open) {
      setTagLoading(true);
      setTagError(null);
      apiFetch('/tags')
        .then(tags => setAllTags(tags))
        .catch(() => setTagError('Fehler beim Laden der Tags'))
        .finally(() => setTagLoading(false));
      setNewTagName('');
      setNewTagColor('#1976d2');
      setShowAddUI(false);
    }
  }, [open]);

  // Add existing tag to player
  const handleSelectTag = async (tag) => {
    // Prevent adding if already assigned
    if (player.tags && player.tags.some(t => t.id === tag.id)) return;
    setAdding(true);
    try {
      await apiFetch(`/players/${player.id}/tags`, { method: 'POST', body: { tag_id: tag.id } });
      if (onTagAdded) onTagAdded(tag);
    } catch {
      setTagError('Tag konnte nicht hinzugefügt werden');
    } finally {
      setAdding(false);
    }
  };

  // Create new tag and add to player
  const handleCreateTag = async () => {
    if (!newTagName) return;
    setAdding(true);
    setTagError(null);
    try {
      const tag = await apiFetch('/tags', { method: 'POST', body: { name: newTagName, color: newTagColor } });
      setAllTags([...allTags, tag]);
      await apiFetch(`/players/${player.id}/tags`, { method: 'POST', body: { tag_id: tag.id } });
      setNewTagName('');
      setNewTagColor('#1976d2');
      setShowAddUI(false);
      if (onTagAdded) onTagAdded(tag);
    } catch {
      setTagError('Tag konnte nicht erstellt werden');
    } finally {
      setAdding(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Tags verwalten</DialogTitle>
      <DialogContent>
        {tagLoading ? <CircularProgress size={24} /> : null}
        {tagError && <Typography color="error">{tagError}</Typography>}
        <Typography variant="subtitle1" sx={{ mb: 1 }}>Vorhandene Tags:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          {allTags.length === 0 ? (
            <Typography color="text.secondary">Keine Tags vorhanden</Typography>
          ) : (
            allTags.map(tag => {
              const bg = tag.color || undefined;
              const fg = getContrastColor(bg);
              return (
                <Chip
                  key={tag.id}
                  label={tag.name}
                  style={{
                    backgroundColor: bg,
                    color: fg,
                    border: '1px solid rgba(0,0,0,0.2)'
                  }}
                  onClick={() => handleSelectTag(tag)}
                  clickable
                  sx={{ mb: 0.5 }}
                  disabled={adding}
                />
              );
            })
          )}
        </Box>
        <Box sx={{ mt: 3 }}>
          {!showAddUI ? (
            <Button
              variant="outlined"
              color="primary"
              onClick={() => setShowAddUI(true)}
              sx={{ mb: 2 }}
            >
              Tag hinzufügen
            </Button>
          ) : (
            <>
              <TextField
                label="Tag-Name"
                value={newTagName}
                onChange={e => setNewTagName(e.target.value)}
                variant="outlined"
                sx={{ mb: 2, mt: 1 }}
                disabled={adding}
              />
              <Typography variant="subtitle2">Farbe wählen:</Typography>
              <SketchPicker
                color={newTagColor}
                onChangeComplete={color => setNewTagColor(color.hex)}
                presetColors={["#1976d2", "#388e3c", "#fbc02d", "#d32f2f", "#7b1fa2", "#455a64"]}
                disableAlpha
              />
              <Button
                variant="contained"
                color="primary"
                sx={{ mt: 2 }}
                onClick={handleCreateTag}
                disabled={adding || !newTagName}
              >
                Tag erstellen und zuweisen
              </Button>
              <Button
                variant="text"
                sx={{ mt: 1, ml: 2 }}
                onClick={() => setShowAddUI(false)}
              >
                Abbrechen
              </Button>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Schließen</Button>
      </DialogActions>
    </Dialog>
  );
}
