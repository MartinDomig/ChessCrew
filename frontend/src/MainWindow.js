import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EmailIcon from '@mui/icons-material/Email';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import FilterListIcon from '@mui/icons-material/FilterList';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import PeopleIcon from '@mui/icons-material/People';
import SportsScoreIcon from '@mui/icons-material/SportsScore';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import React, {useState} from 'react';

import {apiFetch} from './api';
import BurgerMenu from './BurgerMenu';
import {exportEmailList} from './csvUtils';
import ImportDialog from './ImportDialog';
import PlayerDetails from './PlayerDetails';
import PlayerList from './PlayerList';
import {PlayerListProvider, usePlayerList} from './PlayerListContext';
import TournamentDetails from './TournamentDetails';
import TournamentImportDialog from './TournamentImportDialog';
import TournamentList from './TournamentList';
import {TournamentListProvider, useTournamentList} from './TournamentListContext';

function MainWindowContent({user}) {
  // Tab state: 0 = players, 1 = tournaments
  const [tab, setTab] = useState(0);
  const [importOpen, setImportOpen] = useState(false);
  const handleImportClick = () => setImportOpen(true);
  const [tournamentImportOpen, setTournamentImportOpen] = useState(false);
  const handleImportTournamentResults = () => setTournamentImportOpen(true);
  const isAdmin = user && user.admin;
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedTournament, setSelectedTournament] = useState(null);
  const isTabletOrLarger = useMediaQuery('(min-width: 768px)');
  const {players, reloadPlayers, updatePlayer, activeOnly, setActiveOnly} =
      usePlayerList();
  const {tournaments, reloadTournaments} = useTournamentList();

  // On mobile, show either master or detail for current tab
  const showPlayerMaster =
      tab === 0 && (isTabletOrLarger || selectedPlayer === null);
  const showPlayerDetail =
      tab === 0 && (isTabletOrLarger || selectedPlayer !== null);
  const showTournamentMaster =
      tab === 1 && (isTabletOrLarger || selectedTournament === null);
  const showTournamentDetail =
      tab === 1 && (isTabletOrLarger || selectedTournament !== null);

  const handleBack = () => {
    if (tab === 0)
      setSelectedPlayer(null);
    else
      setSelectedTournament(null);
  };

  const handleLogout = async () => {
    try {
      await apiFetch('/logout', {method: 'POST'});
      window.location.reload();
    } catch (err) {
      // Optionally show an error message
    }
  };

  // Tab icons for mobile UI
  const tabIcons = [<PeopleIcon />, <EmojiEventsIcon />];

  return (
    <Box sx={{
    height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position='fixed' sx={{
    width: '100%' }}>
        <Toolbar>
          {!isTabletOrLarger && ((tab === 0 && selectedPlayer) || (tab === 1 && selectedTournament)) && (
            <IconButton edge='start' color='inherit' onClick={handleBack}>
              <ArrowBackIcon />
            </IconButton>
          )}
          <Tabs
  value = {tab} onChange = {
    (_, v) => {
      setTab(v);
      setSelectedPlayer(null);
      setSelectedTournament(null);
    }
  } sx = {
    { minHeight: 48 }
  } textColor = 'inherit'
  indicatorColor = 'secondary'
            slotProps={{
    indicator: {style: {height: 3}} }}
          >
            <Tab icon={<PeopleIcon />} sx={
    { minWidth: 48 }} />
            <Tab icon={<EmojiEventsIcon />
}
sx = {
  {
    minWidth: 48
  }
} />
          </Tabs > <Box sx = {
       {
         ml: 'auto'
       }
     }><BurgerMenu onLogout = {handleLogout} />
          </Box>
    <ImportDialog open = {importOpen} onClose =
         {() => setImportOpen(false)} onImported =
             {reloadPlayers} />
          <TournamentImportDialog open={tournamentImportOpen} onClose={() => setTournamentImportOpen(false)} onImported={
    reloadTournaments} />
    </Toolbar>
      </AppBar><Box sx = {
       {
         flex: 1, display: 'flex', overflow: 'hidden', mt: 8
       }
     }> {showPlayerMaster && (
          <Box
            sx={{
    width: {xs: '100%', md: 320},
        borderRight: isTabletOrLarger ? '1px solid #ddd' : 'none',
        display: {xs: selectedPlayer ? 'none' : 'block', md: 'block'},
        height: '100%', overflowY: 'auto', position: 'relative',
            }}
          >
            {/* Player-specific actions bar */}
            <Box sx={{
    display: 'flex', gap: 1, p: 1, position: 'sticky', top: 0, zIndex: 1,
        background: '#fafafa', borderBottom: '1px solid #eee',
        alignItems: 'center'
            }}>
              {isAdmin && (
                <IconButton
            color = 'primary'
            onClick = {handleImportClick} size = 'small'
            title = 'Import Meldekartei'
            sx = {
              {
                p: 0.5
              }
            } > <ImportExportIcon fontSize = 'small' />
                </IconButton>
              )}
              <IconButton 
                color="primary" 
                onClick={() => exportEmailList(players)} 
                size="small" 
                title="Export E-Mail Liste"
                sx={{ p: 0.5 }}
              >
                <EmailIcon fontSize="small" />
                </IconButton>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 'auto' }}>
                <FilterListIcon fontSize="small" color="action" /><
                Switch
            edge = 'end'
            checked = {activeOnly} onChange = {
                (_, checked) => setActiveOnly(checked)} color = 'primary'
                  size='small'
                />
              </Box>
            </Box>
            <PlayerList players={players} onPlayerClick={
    setSelectedPlayer} />
          </Box>
        )
}
{showPlayerDetail && selectedPlayer && (
          <PlayerDetails player={selectedPlayer} onPlayerUpdated={
      updatePlayer} />
        )}
        {/* Master/Detail for Tournaments */}
        {showTournamentMaster && (
          <Box
            sx={{
              width: { xs: '100%', md: 320 },
              borderRight: isTabletOrLarger ? '1px solid #ddd' : 'none',
              display: { xs: selectedTournament ? 'none' : 'block', md: 'block' },
              height: '100%', 
              overflowY: 'auto',
              position: 'relative',
            }}
          >
            {/* Tournament-specific actions bar */}
            <Box sx={{ 
              display: 'flex', 
              gap: 1, 
              p: 1, 
              position: 'sticky', 
              top: 0, 
              zIndex: 1, 
              background: '#fafafa', 
              borderBottom: '1px solid #eee',
              alignItems: 'center'
            }}>
              {isAdmin && (
                <IconButton 
                  color="primary" 
                  onClick={handleImportTournamentResults} 
                  size="small" 
                  title="Import Turnierergebnisse"
                  sx={{ p: 0.5 }}
                >
                  <SportsScoreIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
            <TournamentList tournaments={tournaments} onTournamentClick={
      setSelectedTournament} />
          </Box>
        )
}
{
    showTournamentDetail && selectedTournament &&
        (<TournamentDetails tournament =
          {
            selectedTournament
          } />
        )}
      </Box>
         </Box>
  );
}

function MainWindow({ user }) {
  return (
    <PlayerListProvider>
      <TournamentListProvider>
        <MainWindowContent user={user} />
         </TournamentListProvider>
    </PlayerListProvider>);
}

export default MainWindow;
