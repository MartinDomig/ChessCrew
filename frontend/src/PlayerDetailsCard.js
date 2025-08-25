import React, { useEffect, useState } from 'react';
import { IconButton, Card, CardContent, Typography, Button, Box, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import TagManager from './TagManager';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditIcon from '@mui/icons-material/Edit';
import CategoryChip from './CategoryChip';
import TagChip from './TagChip';
import PlayerActiveStar from './PlayerActiveStar';
import { apiFetch } from './api';
import Autocomplete from '@mui/material/Autocomplete';
import PlayerTags from './PlayerTags';

export default function PlayerDetailsCard({ player, onBack, onStatusChange, onPlayerUpdate }) {
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
  const [playerTagsKey, setPlayerTagsKey] = useState(0);

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

  // Fetch all tags when modal opens
  const handleOpenTagModal = () => {
    setTagModalOpen(true);
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
          <IconButton
            color="primary"
            onClick={() => setModalOpen(true)}
            sx={{ ml: 2 }}
            aria-label="Kontakt bearbeiten"
          >
            <EditIcon />
          </IconButton>
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
        <Box sx={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 1, width: '100%' }}>
          <IconButton
            color="primary"
            size="large"
            onClick={handleOpenTagModal}
            aria-label="Tag hinzufügen"
            sx={{ p: 0, alignSelf: 'center', verticalAlign: 'middle' }}
          >
            <AddCircleOutlineIcon fontSize="large" />
          </IconButton>
          {localPlayer.tags && localPlayer.tags.map(tag => (
            <TagChip
              key={`player-${localPlayer.id}-tag-${tag.id}`}
              tag={{ ...tag, name: tag.name ? `${tag.name} ❌` : '' }}
              size="small"
              onClick={async (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (window.confirm(`Tag "${tag.name}" wirklich entfernen?`)) {
                  await apiFetch(`/players/${player.id}/tags/${tag.id}`, { method: 'DELETE' });
                  const updated = await apiFetch(`/players/${player.id}`);
                  setLocalPlayer(updated);
                  setPlayerTagsKey(k => k + 1);
                  if (onPlayerUpdate) onPlayerUpdate(updated);
                }
              }}
            />
          ))}
        </Box>
        <TagManager
          player={player}
          open={tagModalOpen}
          onClose={async () => {
            setTagModalOpen(false);
            const updated = await apiFetch(`/players/${player.id}`);
            setLocalPlayer(updated);
            setPlayerTagsKey(k => k + 1);
            if (onPlayerUpdate) onPlayerUpdate(updated);
          }}
          onTagAdded={
            async () => {
              setTagModalOpen(false);
              const updated = await apiFetch(`/players/${player.id}`);
              setLocalPlayer(updated);
              setPlayerTagsKey(k => k + 1);
              if (onPlayerUpdate) onPlayerUpdate(updated);
            }
          }
        />
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
