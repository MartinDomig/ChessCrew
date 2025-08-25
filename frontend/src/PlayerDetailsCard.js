import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress } from '@mui/material';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import { apiFetch } from './api';

export default function PlayerDetailsCard({ player, onBack, onStatusChange }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

    useEffect(() => {
        setLoading(true);
        setNotes([]);
        setError(null);
        apiFetch(`/players/${player.id}/notes`)
          .then(setNotes)
          .catch(err => setError(err.message))
          .finally(() => setLoading(false));
    }, [player.id]);

  return (
    <Card sx={{ mb: 2, maxWidth: 500, mx: 'auto', position: 'relative' }}>
  <PlayerActiveStar player={player} onStatusChange={onStatusChange} />
      <CardContent>
        <Typography variant="h5" sx={{ mb: 2 }}>
          {player.first_name} {player.last_name}
        </Typography>
        <Box sx={{ mb: 2 }}>
          <CategoryChip player={player} />
        </Box>
        {Object.entries(player).map(([key, value]) => (
          <Typography key={key} sx={{ mb: 1 }}>
            <strong>{key}:</strong> {String(value)}
          </Typography>
        ))}
  {/* ...existing code... (removed Zurück button) */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6">Notizen</Typography>
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
              <Box key={note.id} sx={{ mb: 2, p: 1, border: '1px solid #eee', borderRadius: 1 }}>
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
