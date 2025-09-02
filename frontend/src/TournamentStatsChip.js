import React, { useState, useEffect } from 'react';
import { Chip, CircularProgress } from '@mui/material';
import { EmojiEvents } from '@mui/icons-material';
import { apiFetch } from './api';

export default function TournamentStatsChip({ player }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

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

    // Check if tournament stats are already pre-loaded in player data
    if (player.tournament_stats) {
      setStats({
        points: player.tournament_stats.total_points || 0,
        games: player.tournament_stats.total_games || 0
      });
      return;
    }

    // Fallback: fetch tournament data if not pre-loaded
    setLoading(true);
    apiFetch(`/players/${player.id}/tournaments`)
      .then(tournaments => {
        // Calculate total points and games across all tournaments
        const totalPoints = tournaments.reduce((sum, t) => sum + (t.points || 0), 0);
        const totalGames = tournaments.reduce((sum, t) => sum + (t.games_played || 0), 0);

        setStats({ points: totalPoints, games: totalGames });
        setLoading(false);
      })
      .catch(() => {
        setStats({ points: 0, games: 0 });
        setLoading(false);
      });
  }, [player?.id, player?.tournament_stats]);

  if (loading) {
    return (
      <Chip
        icon={<CircularProgress size={12} />}
        label="..."
        size="small"
        variant="outlined"
      />
    );
  }

  if (!stats || (stats.points === 0 && stats.games === 0)) {
    return null; // Don't show chip if no tournament data
  }

  const label = `${formatPoints(stats.points)}/${stats.games}`;

  return (
    <Chip
      icon={<EmojiEvents fontSize="small" />}
      label={label}
      size="small"
      variant="outlined"
      color="white"
    />
  );
}
