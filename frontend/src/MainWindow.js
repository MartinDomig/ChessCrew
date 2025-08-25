import React, { useEffect, useState } from 'react';
import { AppBar, Toolbar, IconButton, Typography, Box, Container, Menu, MenuItem, ListItemIcon, Drawer, Switch } from '@mui/material';
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

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  useEffect(() => {
    if (search || debouncedSearch) {
      const handler = setTimeout(() => {
        console.log('Set debounced search:', search)
        setDebouncedSearch(search);
      }, 300);
      return () => clearTimeout(handler);
    }
  }, [search]);

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
          {/* Back button on the left if a player is selected */}
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
          {/* Burger menu button on the right */}
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
      <Toolbar /> {/* Spacer for fixed AppBar */}
      {/* Search bar below AppBar */}
      {!selectedPlayer && (
        <Box sx={{ px: 2, py: 1, background: '#fafafa', borderBottom: '1px solid #eee' }}>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Spieler suchen..."
            style={{ width: '100%', padding: '8px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ccc' }}
            autoComplete="off"
            autoFocus
          />
        </Box>
      )}
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
          />
        ) : loading ? (
          <Typography>Loading players...</Typography>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : (
          players
            .filter(player => {
              const name = `${player.first_name} ${player.last_name}`.toLowerCase();
              const kat = (player.kat || "").toLowerCase();
              const terms = debouncedSearch.toLowerCase().split(/\s+/).filter(Boolean);
              return terms.length === 0 || terms.some(term => name.includes(term) || kat.includes(term));
            })
            .map(player => (
              <div key={player.id} onClick={() => setSelectedPlayer(player)} style={{ cursor: 'pointer' }}>
                <PlayerCard
                  player={player}
                  onStatusChange={isActive => {
                    setPlayers(players => players.map(p =>
                      p.id === player.id ? { ...p, is_active: isActive } : p
                    ));
                  }}
                />
              </div>
            ))
        )}
      </Container>
    </Box>
  );
}
