import React, { useEffect, useState } from 'react';
import { Box, Chip } from '@mui/material';
import { apiFetch } from './api';

export default function PlayerTags({ player, onTagClick }) {
  if (!player.tags || !player.tags.length) return null;

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
      {player.tags.map(tag => (
        <Chip
          key={`player-${player.id}-tag-${tag.id}`}
          label={tag.name}
          style={{ backgroundColor: tag.color || undefined, color: '#fff' }}
          onClick={onTagClick ? (e => { e.preventDefault(); e.stopPropagation(); onTagClick(tag); }) : undefined}
        />
      ))}
    </Box>
  );
}
