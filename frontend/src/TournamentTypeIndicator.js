import React from 'react';
import { Chip } from '@mui/material';
import { EmojiEvents, Star } from '@mui/icons-material';

export default function TournamentTypeIndicator({ tournament, size = 'small' }) {
  if (!tournament) return null;

  // Determine if tournament is rated based on elo_rating field
  const isRated = tournament.elo_rating !== null && tournament.elo_rating !== undefined;

  let label = '';
  if (isRated) {
    const eloRating = tournament.elo_rating.toLowerCase();
    const words = eloRating.split(' ');
    for (const word of words) {
        if (word.length > 0 && word.toLowerCase().includes('national'))
            label += word[0].toUpperCase();
    }
  } else {
    label = '-';
  }

  return (
    <Chip
      icon={isRated ? <Star fontSize="small" /> : <EmojiEvents fontSize="small" />}
      label={label}
      size={size}
      variant="outlined"
      sx={isRated ? {
        borderColor: '#B8860B',
        color: '#B8860B',
        '& .MuiChip-icon': {
          color: '#B8860B'
        }
      } : {}}
    />
  );
}
