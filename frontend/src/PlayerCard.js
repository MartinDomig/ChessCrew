import React, { useState } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import PlayerTags from './PlayerTags';

export default function PlayerCard({ player, onStatusChange, onTagClick, onCategoryClick }) {
  return (
    <Card sx={{ mb: 2, position: 'relative' }}>
      <PlayerActiveStar player={player} onStatusChange={onStatusChange} />
      <CardContent>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6">
            {player.first_name} {player.last_name}
          </Typography>
          <CategoryChip player={player} onClick={onCategoryClick} />
        </Box>
        <PlayerTags player={player} onTagClick={onTagClick} />
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
