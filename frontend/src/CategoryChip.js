import React from 'react';
import { Chip } from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

function willMoveUp(player) {
  if (!player?.kat || !player?.birthday) return false;

  // Calculate category from birth year
  const today = new Date();
  const currentYear = today.getFullYear();
  // Stichtag: 1.1. (so next year is always currentYear + 1)
  let birthYear;
  if (typeof player.birthday === 'string') {
    // Try to parse with Date
    const dateObj = new Date(player.birthday);
    if (!isNaN(dateObj.getTime())) {
      birthYear = dateObj.getFullYear();
    } else {
      // Fallback: try to extract year from string
      const match = player.birthday.match(/\d{4}/);
      birthYear = match ? parseInt(match[0], 10) : null;
    }
  } else if (player.birthday instanceof Date) {
    birthYear = player.birthday.getFullYear();
  } else {
    birthYear = null;
  }
  if (!birthYear) return false;
  const ageThisYear = currentYear - birthYear;

  // player.kat is U8, U10, S65 or somesuch. The number in that string is the max age for the category.
  // return true if the players current age is that number, false otherwise
  const maxAge = parseInt(player.kat.slice(1), 10);
  return ageThisYear === maxAge;
}

export default function CategoryChip({ player }) {
  if (!player?.kat) return null;

  return (
    <Chip
      label={player.kat + (willMoveUp(player) ? " >" : "")}
      color={player.female ? "secondary" : "primary"}
      size="small"
    />
  );
}
