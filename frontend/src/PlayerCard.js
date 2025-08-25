import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

export default function PlayerCard({ player }) {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6">{player.first_name}</Typography>
        <Typography color="text.secondary">ID: {player.id}</Typography>
        <Typography color="text.secondary">ELO: {player.elo}</Typography>
      </CardContent>
    </Card>
  );
}
