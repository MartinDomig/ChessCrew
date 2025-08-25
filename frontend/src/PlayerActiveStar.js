import React, { useState } from 'react';
import StarIcon from '@mui/icons-material/Star';
import { apiFetch } from './api';

export default function PlayerActiveStar({ player, onStatusChange }) {
  const [isActive, setIsActive] = useState(player.is_active);

  const handleToggle = async (e) => {
    e.stopPropagation();
    try {
      const updated = await apiFetch(`/players/${player.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !isActive })
      });
      setIsActive(updated.is_active);
      if (onStatusChange) onStatusChange(updated.is_active);
    } catch (err) {
      // Optionally show error
    }
  };

  return (
    <StarIcon
      sx={{ position: 'absolute', top: 8, right: 8, color: isActive ? 'gold' : 'grey', cursor: 'pointer' }}
      onClick={handleToggle}
    />
  );
}
