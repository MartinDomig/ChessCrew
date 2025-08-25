import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import { apiFetch } from './api';

export default function PlayerCard({ player: initialPlayer }) {
  const [player, setPlayer] = useState(initialPlayer);

  const handleToggleActive = async () => {
    try {
      const updated = await apiFetch(`/players/${player.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !player.is_active })
      });
      setPlayer(updated);
    } catch (err) {
      // Optionally show error
    }
  };

  return (
    <Card sx={{ mb: 2, position: 'relative' }}>
      <StarIcon
        sx={{ position: 'absolute', top: 8, right: 8, color: player.is_active ? 'gold' : 'grey', cursor: 'pointer' }}
        onClick={handleToggleActive}
      />
      <CardContent>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6">
            {player.first_name} {player.last_name}
          </Typography>
          {player.kat && (
            <Chip label={player.kat} color="primary" size="small" />
          )}
        </Box>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {`Rating: ${player.elo ?? ''} / ${player.fide_elo ?? ''}`}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Verein: {player.club}
        </Typography>
      </CardContent>
    </Card>
  );
}
