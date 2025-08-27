import React, { useState } from 'react';
import { PlayerListProvider, usePlayerList } from './PlayerListContext';
import BurgerMenu from './BurgerMenu';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { apiFetch } from './api';
import PlayerList from './PlayerList';
import PlayerDetails from './PlayerDetails';
import ImportDialog from './ImportDialog';

function MainWindowContent({ user }) {
  const [importOpen, setImportOpen] = useState(false);
  const handleImportClick = () => setImportOpen(true);
  const isAdmin = user && user.admin;
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const isTabletOrLarger = useMediaQuery('(min-width: 768px)');
  const { players, reloadPlayers, updatePlayer, activeOnly, setActiveOnly } = usePlayerList();

  // On mobile, show either master or detail
  const showMaster = isTabletOrLarger || selectedPlayer === null;
  const showDetail = isTabletOrLarger || selectedPlayer !== null;

  const handleBack = () => setSelectedPlayer(null);

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
      <AppBar position="fixed" sx={{ width: '100%' }}>
        <Toolbar>
          {!isTabletOrLarger && selectedPlayer && (
            <IconButton edge="start" color="inherit" onClick={handleBack}>
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ChessCrew
          </Typography>
          <BurgerMenu
            isAdmin={isAdmin}
            onImportClick={handleImportClick}
            showActiveOnly={activeOnly}
            onShowActiveChange={setActiveOnly}
            onLogout={handleLogout}
          />
          <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} onImported={reloadPlayers} />
        </Toolbar>
      </AppBar>
      {/* Add marginTop to avoid AppBar overlap */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden', mt: 8 }}>
        {/* Master: Player List */}
        {showMaster && (
          <Box
            sx={{
              width: { xs: '100%', md: 320 },
              borderRight: isTabletOrLarger ? '1px solid #ddd' : 'none',
              display: { xs: selectedPlayer ? 'none' : 'block', md: 'block' },
              height: '100%',
              overflowY: 'auto',
            }}
          >
            <PlayerList players={players} onPlayerClick={setSelectedPlayer} />
          </Box>
        )}
        {/* Detail: Player Details */}
        {showDetail && selectedPlayer && (
          <PlayerDetails player={selectedPlayer} onPlayerUpdated={updatePlayer} />
        )}
      </Box>
    </Box>
  );
}

function MainWindow({ user }) {
  return (
    <PlayerListProvider>
      <MainWindowContent user={user} />
    </PlayerListProvider>
  );
}

export default MainWindow;
