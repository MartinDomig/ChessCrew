import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { apiFetch } from './api';
import PlayerActiveStar from './PlayerActiveStar';

export default function PlayerCard({ player: initialPlayer }) {
  const [player, setPlayer] = useState(initialPlayer);

  return (
    <Card sx={{ mb: 2, position: 'relative' }}>
      <PlayerActiveStar player={player} onStatusChange={active => setPlayer({ ...player, is_active: active })} />
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
