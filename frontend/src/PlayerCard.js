import React, { useState } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import TagChip from './TagChip';

export default function PlayerCard({ player, onStatusChange, onTagClick, onCategoryClick }) {
  let playerElo = (player.elo > 0 ? `ELO: ${player.elo}` : '');
  if(player.fide_elo > 0) {
    playerElo += (player.elo > 0 ? ' ' : '') + `FIDE: ${player.fide_elo}`;
  }

  const bgColor = player.active ? '#e3f2fd' : '#f5f7fa';
  return (
    <Card sx={{ mb: 1, p: 1, height: 102, position: 'relative', background: bgColor }}>
      {/* Top right PlayerActiveStar */}
      <Box sx={{ position: 'absolute', top: 8, right: 8, zIndex: 2 }}>
        <PlayerActiveStar player={player} onStatusChange={onStatusChange} />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
        {/* First row: Name */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, fontSize: '1.25rem' }}>
            {player.last_name} {player.first_name}
          </Typography>
        </Box>
        {/* Second row: Club, Rating */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mt: 0.5 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.95rem', mr: 2 }}>
            {player.club}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              fontSize: '0.95rem',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: 120
            }}
          >
            {playerElo}
          </Typography>
        </Box>
        {/* Third row: Category, Tags */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mt: 0.5 }}>
          <CategoryChip player={player} onClick={onCategoryClick} />
          <Box sx={{ display: 'flex', flexWrap: 'nowrap', gap: 0.5, overflow: 'hidden', minWidth: 80 }}>
            {player.tags && player.tags.map(tag => (
              <TagChip
                key={`player-${player.id}-tag-${tag.id}`}
                tag={tag}
                size="small"
                onClick={onTagClick ? (e => { e.preventDefault(); e.stopPropagation(); onTagClick(tag); }) : undefined}
              />
            ))}
          </Box>
        </Box>
      </Box>
    </Card>
  );
}
