import React, { useEffect, useState } from 'react';
import { AppBar, Toolbar, IconButton, Typography, Box, Container, Menu, MenuItem, ListItemIcon, Drawer, Switch } from '@mui/material';
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
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showActiveOnly, setShowActiveOnly] = useState(true);

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

  useEffect(() => {
    setLoading(true);
    setError('');
    const param = showActiveOnly ? '?active=true' : '';
    apiFetch(`/players${param}`)
      .then(setPlayers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [showActiveOnly]);

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
  const handleLogout = async () => {
    try {
      await apiFetch('/logout', { method: 'POST' });
      window.location.reload();
    } catch (err) {
      // Optionally show an error message
    }
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
            <MenuItem>
              <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                Nur aktive Spieler anzeigen
                <Switch
                  edge="end"
                  checked={showActiveOnly}
                  onChange={(_, checked) => setShowActiveOnly(checked)}
                  color="primary"
                />
              </Box>
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              Logout
            </MenuItem>
          </Menu>
          <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ChessCrew
          </Typography>
        </Toolbar>
      </AppBar>
      <Toolbar /> {/* Spacer for fixed AppBar */}
      <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <MenuItem onClick={() => setImportOpen(true)}>
          <ListItemIcon><ImportExportIcon /></ListItemIcon>
          Meldekartei importieren
        </MenuItem>
        <MenuItem>
          <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Nur aktive Spieler anzeigen
            <Switch
              edge="end"
              checked={showActiveOnly}
              onChange={(_, checked) => setShowActiveOnly(checked)}
              color="primary"
            />
          </Box>
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon></ListItemIcon>
          Logout
        </MenuItem>
      </Drawer>
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
