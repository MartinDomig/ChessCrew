import React, { useState } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import TagChip from './TagChip';

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
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {`Rating: ${player.elo ?? ''} / ${player.fide_elo ?? ''}`}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Verein: {player.club}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'row',
            flexWrap: 'nowrap',
            gap: 1,
            mt: 1,
            width: '100%',
            overflow: 'hidden',
          }}
        >
          {player.tags && player.tags.map(tag => (
            <TagChip
              key={`player-${player.id}-tag-${tag.id}`}
              tag={{ ...tag, name: tag.name ? tag.name[0] : '' }}
              size="small"
              onClick={onTagClick ? (e => { e.preventDefault(); e.stopPropagation(); onTagClick(tag); }) : undefined}
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}
