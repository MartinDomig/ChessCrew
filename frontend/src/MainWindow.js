import React, { useEffect, useState } from 'react';
import PlayerList from './PlayerList';
import { AppBar, Toolbar, IconButton, Typography, Box, Container, CircularProgress, Menu, MenuItem, ListItemIcon, Drawer, Switch } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import FilterListIcon from '@mui/icons-material/FilterList';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import MenuIcon from '@mui/icons-material/Menu';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import ImportDialog from './ImportDialog';
import PlayerCard from './PlayerCard';
import PlayerDetailsCard from './PlayerDetailsCard';
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
  const [selectedPlayer, setSelectedPlayer] = useState(null);

  useEffect(() => {
    apiFetch('/session/user')
      .then(data => setIsAdmin(data && data.admin))
      .catch(() => setIsAdmin(false));
  }, []);

  const reloadPlayers = () => {
    setLoading(true);
    setError('');
    const param = showActiveOnly ? '?active=true' : '';
    apiFetch(`/players${param}`)
      .then(setPlayers)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reloadPlayers();
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

  const handlePlayerUpdate = (updatedPlayer) => {
    setPlayers(players => players.map(p => p.id === updatedPlayer.id ? updatedPlayer : p));
    setSelectedPlayer(updatedPlayer);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="fixed">
        <Toolbar>
          {selectedPlayer ? (
            <IconButton edge="start" color="inherit" aria-label="back" sx={{ mr: 2 }} onClick={() => setSelectedPlayer(null)}>
              <ArrowBackIcon />
            </IconButton>
          ) : (
            <Box sx={{ width: 40, mr: 2 }} />
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ChessCrew
          </Typography>
          <IconButton edge="end" color="inherit" aria-label="menu" sx={{ ml: 2 }} onClick={handleMenuOpen}>
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
              <ListItemIcon>
                <FilterListIcon />
              </ListItemIcon>
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
              <ListItemIcon>
                <LogoutIcon />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
          <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} />
        </Toolbar>
      </AppBar>
      <Toolbar />
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
        {selectedPlayer ? (
          <PlayerDetailsCard
            player={selectedPlayer}
            onBack={() => setSelectedPlayer(null)}
            onStatusChange={isActive => {
              setPlayers(players => players.map(p =>
                p.id === selectedPlayer.id ? { ...p, is_active: isActive } : p
              ));
              setSelectedPlayer(sp => sp ? { ...sp, is_active: isActive } : sp);
            }}
            onPlayerUpdate={handlePlayerUpdate}
          />
        ) : loading ? (
          <CircularProgress size={24} sx={{ mr: 2 }} />
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : (
          <PlayerList
            players={players}
            onPlayerClick={setSelectedPlayer}
            onStatusChange={(id, isActive) => {
              setPlayers(players => players.map(p =>
                p.id === id ? { ...p, is_active: isActive } : p
              ));
            }}
          />
        )}
      </Container>
    </Box>
  );
}
