import React, { useEffect, useState } from 'react';
import { AppBar, Toolbar, IconButton, Typography, Box, Container } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import PlayerCard from './PlayerCard';
import { apiFetch } from './api';

export default function MainWindow() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/players')
      .then(setPlayers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton edge="start" color="inherit" aria-label="menu" sx={{ mr: 2 }}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ChessCrew
          </Typography>
        </Toolbar>
      </AppBar>
      <Toolbar /> {/* Spacer for fixed AppBar */}
      <Container sx={{ flex: 1, overflowY: 'auto', mt: 2 }}>
        {loading ? (
          <Typography>Loading players...</Typography>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : (
          players.map(player => <PlayerCard key={player.id} player={player} />)
        )}
      </Container>
    </Box>
  );
}
