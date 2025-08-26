import React, { useState } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import CategoryChip from './CategoryChip';
import PlayerActiveStar from './PlayerActiveStar';
import TagChip from './TagChip';

export default function PlayerCard({ player, onStatusChange, onTagClick, onCategoryClick }) {
  return (
    <Card sx={{ mb: 1, p: 1, minHeight: 56, boxShadow: 1 }}>
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
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.95rem' }}>
            {player.elo > 0 ? `ELO: ${player.elo}` : ''} {player.fide_elo > 0 ? `FIDE: ${player.fide_elo}` : ''}
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
