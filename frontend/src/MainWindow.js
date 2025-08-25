import React, { useEffect, useState } from 'react';
import { AppBar, Toolbar, IconButton, Typography, Box, Container, Menu, MenuItem, ListItemIcon } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import ImportDialog from './ImportDialog';
import PlayerCard from './PlayerCard';
import { apiFetch } from './api';

export default function MainWindow() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [importOpen, setImportOpen] = useState(false);

  useEffect(() => {
    apiFetch('/players')
      .then(setPlayers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    apiFetch('/session/user')
      .then(data => setIsAdmin(data && data.admin))
      .catch(() => setIsAdmin(false));
  }, []);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  const handleImportClick = () => {
    setImportOpen(true);
    handleMenuClose();
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton edge="start" color="inherit" aria-label="menu" sx={{ mr: 2 }} onClick={handleMenuOpen}>
            <MenuIcon />
          </IconButton>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
            <MenuItem disabled={!isAdmin} onClick={handleImportClick}>
              <ListItemIcon>
                <ImportExportIcon />
              </ListItemIcon>
              Import Meldekartei
            </MenuItem>
          </Menu>
          <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} />
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
