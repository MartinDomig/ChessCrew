import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import { apiFetch } from './api';
import Autocomplete from '@mui/material/Autocomplete';

export default function PlayerDetailsCard({ player, onBack, onStatusChange }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [email, setEmail] = useState(player.email || '');
  const [phone, setPhone] = useState(player.phone || '');
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [localPlayer, setLocalPlayer] = useState(player);
  const [tagModalOpen, setTagModalOpen] = useState(false);
  const [allTags, setAllTags] = useState([]);
  const [playerTags, setPlayerTags] = useState(player.tags || []);
  const [tagInput, setTagInput] = useState('');
  const [tagLoading, setTagLoading] = useState(false);
  const [tagError, setTagError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setNotes([]);
    setError(null);
    apiFetch(`/players/${player.id}/notes`)
      .then(setNotes)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
    setEmail(player.email || '');
    setPhone(player.phone || '');
    setLocalPlayer(player);
    setModalOpen(false);
  }, [player.id]);

  useEffect(() => {
    setPlayerTags(player.tags || []);
  }, [player.id]);

  // Fetch all tags when modal opens
  const handleOpenTagModal = async () => {
    setTagModalOpen(true);
    setTagLoading(true);
    setTagError(null);
    try {
      const tags = await apiFetch('/tags'); // expects [{id, name, color}]
      setAllTags(tags);
    } catch (err) {
      setTagError('Fehler beim Laden der Tags');
    } finally {
      setTagLoading(false);
    }
  };

  // Save handler for modal
  const handleModalSave = async () => {
    setSaveLoading(true);
    setSaveError(null);
    try {
      await apiFetch(`/players/${player.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ email, phone }),
        headers: { 'Content-Type': 'application/json' },
      });
      setModalOpen(false);
      setLocalPlayer({ ...localPlayer, email, phone });
      // Reload notes after edit
      setLoading(true);
      setNotes([]);
      setError(null);
      apiFetch(`/players/${player.id}/notes`)
        .then(setNotes)
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaveLoading(false);
    }
  };

  // Add tag to player (existing or new)
  const handleAddTag = async (tagName) => {
    setTagLoading(true);
    setTagError(null);
    try {
      // If tag exists, use it; else create
      let tag = allTags.find(t => t.name === tagName);
      if (!tag) {
        tag = await apiFetch('/tags', { method: 'POST', body: JSON.stringify({ name: tagName }) });
        setAllTags([...allTags, tag]);
      }
      await apiFetch(`/players/${player.id}/tags`, { method: 'POST', body: JSON.stringify({ tag_id: tag.id }) });
      setPlayerTags([...playerTags, tag]);
      setTagInput('');
    } catch (err) {
      setTagError('Tag konnte nicht hinzugefügt werden');
    } finally {
      setTagLoading(false);
    }
  };

  // Remove tag from player
  const handleRemoveTag = async (tagId) => {
    setTagLoading(true);
    setTagError(null);
    try {
      await apiFetch(`/players/${player.id}/tags/${tagId}`, { method: 'DELETE' });
      setPlayerTags(playerTags.filter(t => t.id !== tagId));
    } catch (err) {
      setTagError('Tag konnte nicht entfernt werden');
    } finally {
      setTagLoading(false);
    }
  };

  return (
    <Card sx={{ mb: 2, maxWidth: 500, mx: 'auto', position: 'relative' }}>
      <PlayerActiveStar player={player} onStatusChange={onStatusChange} />
      <CardContent>
        <Typography color="text.secondary">
          <small>{player.p_number ? `ID: ${player.p_number}` : ''} {player.fide_number ? ` FIDE: ${player.fide_number}` : ''}</small>
        </Typography>
        <Typography variant="h5">
          {player.first_name} {player.last_name} {player.female ? '(w)' : '(m)'} <CategoryChip player={player} />
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          {player.club}
        </Typography>
        <Typography sx={{ mb: 1 }}>
            <strong>ELO:</strong> {player.elo ?? ''} / {player.fide_elo ?? ''}
        </Typography>
        <Typography sx={{ mb: 1 }}>
            <strong>Geburtsdatum:</strong> {player.birthday ? new Date(player.birthday).toLocaleDateString('de-DE') : ''}
        </Typography>
        <Typography sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
          <strong>E-Mail:</strong>
          <span style={{ marginLeft: 8 }}>
            {localPlayer.email ? <a href={`mailto:${localPlayer.email}`}>{localPlayer.email}</a> : null}
          </span>
        </Typography>
        <Typography sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
          <strong>Telefon:</strong>
          <span style={{ marginLeft: 8 }}>
            {localPlayer.phone ? localPlayer.phone : null}
          </span>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => setModalOpen(true)}
            sx={{ ml: 2 }}
            startIcon={<EditIcon />}
          >Ändern</Button>
        </Typography>
        {saveError && (
          <Typography color="error" sx={{ mb: 1 }}>{saveError}</Typography>
        )}
        <Dialog open={modalOpen} onClose={() => setModalOpen(false)}>
          <DialogTitle>Bearbeite E-Mail und Telefon</DialogTitle>
          <DialogContent>
            <TextField
              label="E-Mail"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              fullWidth
              margin="normal"
            />
            <TextField
              label="Telefon"
              type="text"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              fullWidth
              margin="normal"
            />
            {saveError && (
              <Typography color="error" sx={{ mt: 1 }}>{saveError}</Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setModalOpen(false);
              setEmail(player.email || '');
              setPhone(player.phone || '');
            }}>
              Abbrechen
            </Button>
            <Button onClick={handleModalSave} disabled={saveLoading} variant="contained" color="primary">
              {saveLoading ? 'Speichern...' : 'Speichern'}
            </Button>
          </DialogActions>
        </Dialog>
        <Button
          variant="outlined"
          color="primary"
          onClick={handleOpenTagModal}
          sx={{ mt: 2 }}
        >
          Tags bearbeiten
        </Button>
        <Dialog open={tagModalOpen} onClose={() => setTagModalOpen(false)}>
          <DialogTitle>Tags verwalten</DialogTitle>
          <DialogContent>
            {tagLoading ? <CircularProgress size={24} /> : null}
            {tagError && <Typography color="error">{tagError}</Typography>}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Aktuelle Tags:</Typography>
              {playerTags.length === 0 ? (
                <Typography color="text.secondary">Keine Tags</Typography>
              ) : (
                playerTags.map(tag => (
                  <Box key={tag.id} sx={{ display: 'inline-block', mr: 1, mb: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      style={{ backgroundColor: tag.color || undefined }}
                      onClick={() => handleRemoveTag(tag.id)}
                    >
                      {tag.name} ×
                    </Button>
                  </Box>
                ))
              )}
            </Box>
            <Autocomplete
              freeSolo
              options={allTags.map(t => t.name)}
              value={tagInput}
              onInputChange={(_, v) => setTagInput(v)}
              onChange={(_, v) => v && handleAddTag(v)}
              renderInput={(params) => (
                <TextField {...params} label="Tag hinzufügen" variant="outlined" />
              )}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setTagModalOpen(false)}>Schließen</Button>
          </DialogActions>
        </Dialog>
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Notizen</Typography>
          {loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              <Typography>Lade Notizen...</Typography>
            </Box>
          ) : error ? (
            <Typography color="error">Fehler beim Laden der Notizen: {error}</Typography>
          ) : notes.length === 0 ? (
            <Typography color="text.secondary">Keine Notizen vorhanden.</Typography>
          ) : (
            notes.map(note => (
              <Box key={note.id} sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {note.created_at}
                </Typography>
                <Typography>{note.content}</Typography>
              </Box>
            ))
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
