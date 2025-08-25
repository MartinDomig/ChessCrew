import React, { useEffect, useState } from 'react';
import { Box, Chip } from '@mui/material';
import { apiFetch } from './api';

export default function PlayerTags({ player, onTagClick }) {
  const [tags, setTags] = useState([]);

  useEffect(() => {
    if (player?.id) {
      apiFetch(`/players/${player.id}/tags`)
        .then(setTags);
    }
  }, [player?.id]);

  if (!tags.length) return null;
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
      {tags.map(tag => (
        <Chip
          key={tag.id}
          label={tag.name}
          style={{ backgroundColor: tag.color || undefined, color: '#fff' }}
          onClick={onTagClick ? () => onTagClick(tag) : undefined}
        />
      ))}
    </Box>
  );
}
