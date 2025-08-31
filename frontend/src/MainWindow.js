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
import Button from '@mui/material/Button';

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

  const exportEmailList = () => {
    if (!players || players.length === 0) return;
    const header = ['First Name', 'Last Name', 'Email', 'Gender'];
    const rows = [];
    const emailRegex = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
    players.forEach(p => {
      const gender = p.female ? 'female' : 'male';
      const emails = (p.email || '').split(/[,;\s]+/).filter(e => emailRegex.test(e));
      emails.forEach(email => {
        if (email) {
          rows.push([p.first_name, p.last_name, email, gender]);
        }
      });
    });
    if (rows.length === 0) return;
    const csvContent = [header, ...rows]
      .map(row => row.map(field => {
        // Only quote if field contains comma, quote, or newline
        return /[",\n]/.test(field) ? `"${field.replace(/"/g, '""')}` : field;
      }).join(','))
      .join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'players.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
            onExportEmail={exportEmailList}
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
