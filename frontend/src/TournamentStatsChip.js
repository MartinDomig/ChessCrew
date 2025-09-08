import React, { useState, useEffect } from 'react';
import { Chip } from '@mui/material';
import { EmojiEvents, Star } from '@mui/icons-material';

export default function TournamentStatsChip({ player, rated = false }) {
  const [stats, setStats] = useState(null);

  // Helper function to format points with fractions
  const formatPoints = (points) => {
    const wholePart = Math.floor(points);
    const decimalPart = points - wholePart;
    
    if (decimalPart === 0) {
      return wholePart.toString();
    } else if (decimalPart === 0.5) {
      return wholePart === 0 ? '½' : `${wholePart}½`;
    } else if (Math.abs(decimalPart - 0.33) < 0.01) {
      return wholePart === 0 ? '⅓' : `${wholePart}⅓`;
    } else if (Math.abs(decimalPart - 0.67) < 0.01) {
      return wholePart === 0 ? '⅔' : `${wholePart}⅔`;
    } else if (Math.abs(decimalPart - 0.25) < 0.01) {
      return wholePart === 0 ? '¼' : `${wholePart}¼`;
    } else if (Math.abs(decimalPart - 0.75) < 0.01) {
      return wholePart === 0 ? '¾' : `${wholePart}¾`;
    } else {
      return points.toFixed(1);
    }
  };

  useEffect(() => {
    if (!player?.id) return;

    // Use only pre-loaded tournament stats
    if (player.tournament_stats) {
      setStats({
        points: rated ? player.tournament_stats.total_points_rated || 0 : player.tournament_stats.total_points || 0,
        games: rated ? player.tournament_stats.total_games_rated || 0 : player.tournament_stats.total_games || 0
      });
    } else {
      setStats({ points: 0, games: 0,  });
    }
  }, [player?.id, player?.tournament_stats]);

  if (!stats || (stats.points === 0 && stats.games === 0)) {
    return null; // Don't show chip if no tournament data
  }

  const label = `${formatPoints(stats.points)} / ${stats.games}`;

  return (
    <Chip
      icon={rated ? <Star fontSize="small" /> : <EmojiEvents fontSize="small" />}
      label={label}
      size="small"
      variant="outlined"
      color="white"
      sx={rated ? {
        borderColor: '#B8860B',
        color: '#B8860B',
        '& .MuiChip-icon': {
          color: '#B8860B'
        }
      } : {}}
    />
  );
}
