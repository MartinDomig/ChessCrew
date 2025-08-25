import React from 'react';
import { Chip } from '@mui/material';

export default function CategoryChip({ player }) {
  if (!player?.kat) return null;
  console.log('Rendering CategoryChip for player:', player);
  return <Chip label={player.kat} color={player.female ? "secondary" : "primary"} size="small" />;
}
