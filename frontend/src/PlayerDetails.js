import React, { useEffect, useState } from 'react';
import { IconButton, Card, CardContent, Typography, Button, Box, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import TagManager from './TagManager';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditIcon from '@mui/icons-material/Edit';
import CategoryChip from './CategoryChip';
import TagChip from './TagChip';
import PlayerActiveStar from './PlayerActiveStar';
import { apiFetch } from './api';
import PlayerNotes from './PlayerNotes';

export default function PlayerDetailsCard({ player, onPlayerUpdated }) {
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
    setNotes(player.notes || []);
    setLoading(false);
    setError(null);
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
      const updated = { ...localPlayer, email, phone };
      setLocalPlayer(updated);
      if (onPlayerUpdated) onPlayerUpdated(updated);
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

  const onTagDelete = async (tag) => {
    console.log('delte tag', tag);
    try {
       if (window.confirm(`Tag "${tag.name}" wirklich entfernen?`)) {
        await apiFetch(`/players/${player.id}/tags/${tag.id}`, { method: 'DELETE' });
        const updated = await apiFetch(`/players/${player.id}`);
        setLocalPlayer(updated);
        setPlayerTagsKey(prev => prev + 1);
        if (onPlayerUpdated) onPlayerUpdated(updated);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Card sx={{ mb: 2, maxWidth: 500, mx: 'auto', position: 'relative' }}>
      <PlayerActiveStar player={player} />
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
            {localPlayer.email
              ? localPlayer.email
                  .split(/[,;\s]+/)
                  .filter(e => e)
                  .map((email, idx) => (
                    <React.Fragment key={email}>
                      <a href={`mailto:${email}`}>{email}</a>
                      {idx < localPlayer.email.split(/[,;\s]+/).filter(e => e).length - 1 ? ', ' : ''}
                    </React.Fragment>
                  ))
              : null}
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
              tag={tag}
              onDelete={onTagDelete}
              onClick={onTagDelete}
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
            if (onPlayerUpdated) onPlayerUpdated(updated);
          }}
          onTagAdded={
            async () => {
              setTagModalOpen(false);
              const updated = await apiFetch(`/players/${player.id}`);
              setLocalPlayer(updated);
              setPlayerTagsKey(k => k + 1);
              if (onPlayerUpdated) onPlayerUpdated(updated);
            }
          }
        />
        <Box sx={{ mt: 4 }}>
          <PlayerNotes playerId={player.id} />
        </Box>
      </CardContent>
    </Card>
  );
}
