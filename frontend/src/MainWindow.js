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
import React, {useState, useCallback, useEffect} from 'react';

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
import PlayerListSearchBar from './PlayerListSearchBar';

// Navigation types
const NAV_TYPES = {
  PLAYER_LIST: 'player_list',
  TOURNAMENT_LIST: 'tournament_list',
  PLAYER_DETAIL: 'player_detail',
  TOURNAMENT_DETAIL: 'tournament_detail'
};

// Navigation stack hook
function useNavigationStack(initialStack = []) {
  const [stack, setStack] = useState(initialStack);

  const push = useCallback((navObject) => {
    setStack(prev => [...prev, { ...navObject, id: Date.now() + Math.random() }]);
  }, []);

  const pop = useCallback(() => {
    setStack(prev => prev.slice(0, -1));
  }, []);

  const replace = useCallback((navObject) => {
    setStack(prev => [...prev.slice(0, -1), { ...navObject, id: Date.now() + Math.random() }]);
  }, []);

  const clear = useCallback(() => {
    setStack([]);
  }, []);

  const current = stack[stack.length - 1] || null;
  const canGoBack = stack.length > 1;

  return {
    stack,
    current,
    canGoBack,
    push,
    pop,
    replace,
    clear
  };
}

// Navigation renderer component
function NavigationRenderer({ navObject, onNavigate, onPlayerUpdated, onTournamentUpdate, onTournamentDelete, isAdmin, handleImportClick, handleImportTournamentResults, players, tournaments, activeOnly, setActiveOnly, reloadPlayers, reloadTournaments }) {
  if (!navObject) return null;

  const { type, data } = navObject;

  switch (type) {
    case NAV_TYPES.PLAYER_LIST:
      return (
        <Box sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}>
          {/* Fixed search bar */}
          <Box sx={{
            flexShrink: 0,
            px: 1, py: 0.5,
            background: '#fafafa',
            borderBottom: '1px solid #eee',
            position: 'sticky',
            top: 0,
            zIndex: 1
          }}>
            <Box sx={{ mb: 1 }}>
              <PlayerListSearchBar />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {isAdmin && (
                <IconButton
                  color='primary'
                  onClick={handleImportClick}
                  size='small'
                  title='Import Meldekartei'
                  sx={{ p: 0.5 }}
                >
                  <ImportExportIcon fontSize='small' />
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
                <FilterListIcon fontSize="small" color="action" />
                <Switch
                  edge='end'
                  checked={activeOnly}
                  onChange={(_, checked) => setActiveOnly(checked)}
                  color='primary'
                  size='small'
                />
              </Box>
            </Box>
          </Box>
          
          {/* Scrollable content area */}
          <Box sx={{
            flex: 1,
            overflowY: 'auto',
            px: 1,
            py: 0.5
          }}>
            <PlayerList
              players={players}
              onPlayerClick={(player) => onNavigate({
                type: NAV_TYPES.PLAYER_DETAIL,
                data: { player }
              })}
              showSearchBar={false}
            />
          </Box>
        </Box>
      );

    case NAV_TYPES.TOURNAMENT_LIST:
      return (
        <Box sx={{
          width: '100%',
          height: '100%',
          overflowY: 'auto',
          position: 'relative',
        }}>
          {/* Tournament-specific actions bar */}
          <Box sx={{
            display: 'flex',
            gap: 1,
            px: 1, py: 0.5,  // Reduced horizontal padding
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
          <TournamentList
            tournaments={tournaments}
            onTournamentClick={(tournament) => onNavigate({
              type: NAV_TYPES.TOURNAMENT_DETAIL,
              data: { tournament }
            })}
          />
        </Box>
      );

    case NAV_TYPES.PLAYER_DETAIL:
      return (
        <Box sx={{ flex: 1, overflowY: 'auto', height: '100%' }}>
          <PlayerDetails
            player={data.player}
            onPlayerUpdated={onPlayerUpdated}
            onTournamentClick={(tournament, player) => onNavigate({
              type: NAV_TYPES.TOURNAMENT_DETAIL,
              data: { tournament, fromPlayer: player }
            })}
          />
        </Box>
      );

    case NAV_TYPES.TOURNAMENT_DETAIL:
      return (
        <Box sx={{ flex: 1, overflowY: 'auto', height: '100%' }}>
          <TournamentDetails
            tournament={data.tournament}
            onPlayerClick={(player, tournament) => onNavigate({
              type: NAV_TYPES.PLAYER_DETAIL,
              data: { player, fromTournament: tournament }
            })}
            onDelete={onTournamentDelete}
            onUpdate={onTournamentUpdate}
          />
        </Box>
      );

    default:
      return null;
  }
}

function MainWindowContent({user}) {
  const [importOpen, setImportOpen] = useState(false);
  const handleImportClick = () => setImportOpen(true);
  const [tournamentImportOpen, setTournamentImportOpen] = useState(false);
  const handleImportTournamentResults = () => setTournamentImportOpen(true);
  const isAdmin = user && user.admin;
  const isTabletOrLarger = useMediaQuery('(min-width: 768px)');
  const {players, reloadPlayers, updatePlayer, activeOnly, setActiveOnly} = usePlayerList();
  const {tournaments, reloadTournaments} = useTournamentList();

  // Initialize navigation stack with player list
  const navigation = useNavigationStack([{
    type: NAV_TYPES.PLAYER_LIST,
    data: {}
  }]);

  // Handle navigation
  const handleNavigate = useCallback((navObject) => {
    navigation.push(navObject);
  }, [navigation]);

  const handleBack = useCallback(() => {
    navigation.pop();
  }, [navigation]);

  const handleTournamentDelete = useCallback((tournament_id) => {
    // If we're currently viewing the deleted tournament, go back
    if (navigation.current?.type === NAV_TYPES.TOURNAMENT_DETAIL &&
        navigation.current?.data?.tournament?.id === tournament_id) {
      navigation.pop();
    }
  }, [navigation]);

  const handleTournamentUpdate = useCallback((updatedTournament) => {
    // Update the tournament in the current navigation object if it's a tournament detail
    if (navigation.current?.type === NAV_TYPES.TOURNAMENT_DETAIL) {
      navigation.replace({
        ...navigation.current,
        data: { ...navigation.current.data, tournament: updatedTournament }
      });
    }
    reloadTournaments();
  }, [navigation, reloadTournaments]);

  const handleLogout = async () => {
    try {
      await apiFetch('/logout', {method: 'POST'});
      window.location.reload();
    } catch (err) {
      // Optionally show an error message
    }
  };

  // Determine current tab based on navigation
  const currentTab = navigation.current?.type === NAV_TYPES.TOURNAMENT_LIST ||
                    navigation.current?.type === NAV_TYPES.TOURNAMENT_DETAIL ? 1 : 0;

  // Handle tab changes
  const handleTabChange = useCallback((_, newTab) => {
    // Clear navigation stack and search state, then start fresh with the new tab's list
    navigation.clear();
    
    if (newTab === 0) {
      navigation.push({ type: NAV_TYPES.PLAYER_LIST, data: {} });
    } else {
      navigation.push({ type: NAV_TYPES.TOURNAMENT_LIST, data: {} });
    }
  }, [navigation]);

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <AppBar position='fixed' sx={{ width: '100%' }}>
        <Toolbar>
          {navigation.canGoBack && (
            <IconButton edge='start' color='inherit' onClick={handleBack}>
              <ArrowBackIcon />
            </IconButton>
          )}
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            sx={{ minHeight: 48 }}
            textColor='inherit'
            indicatorColor='secondary'
            slotProps={{
              indicator: { style: { height: 3 } }
            }}
          >
            <Tab icon={<PeopleIcon />} sx={{ minWidth: 48 }} />
            <Tab icon={<EmojiEventsIcon />} sx={{ minWidth: 48 }} />
          </Tabs>
          <Box sx={{ ml: 'auto' }}>
            <BurgerMenu onLogout={handleLogout} />
          </Box>
          <ImportDialog
            open={importOpen}
            onClose={() => setImportOpen(false)}
            onImported={reloadPlayers}
          />
          <TournamentImportDialog
            open={tournamentImportOpen}
            onClose={() => setTournamentImportOpen(false)}
            onImported={reloadTournaments}
          />
        </Toolbar>
      </AppBar>

      <Box sx={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        mt: 8
      }}>
        {/* Master/Detail layout for tablet+ */}
        {isTabletOrLarger ? (
          <>
            {/* Master panel */}
            <Box sx={{
              width: { 
                md: 420,  // Increased for tablet landscape
                lg: 480,  // Increased for small desktops
                xl: 520   // Increased for large desktops
              },
              minWidth: 320,
              maxWidth: { md: '35%', lg: '40%', xl: '45%' }, // Percentage-based max width
              borderRight: '1px solid #ddd',
              height: '100%',
              overflowY: 'auto'
            }}>
              <NavigationRenderer
                navObject={
                  navigation.current?.type === NAV_TYPES.PLAYER_DETAIL ?
                    { type: NAV_TYPES.PLAYER_LIST, data: {} } :
                  navigation.current?.type === NAV_TYPES.TOURNAMENT_DETAIL ?
                    { type: NAV_TYPES.TOURNAMENT_LIST, data: {} } :
                  navigation.current
                }
                onNavigate={handleNavigate}
                onPlayerUpdated={updatePlayer}
                onTournamentUpdate={handleTournamentUpdate}
                onTournamentDelete={handleTournamentDelete}
                isAdmin={isAdmin}
                handleImportClick={handleImportClick}
                handleImportTournamentResults={handleImportTournamentResults}
                players={players}
                tournaments={tournaments}
                activeOnly={activeOnly}
                setActiveOnly={setActiveOnly}
                reloadPlayers={reloadPlayers}
                reloadTournaments={reloadTournaments}
              />
            </Box>

            {/* Detail panel */}
            {(navigation.current?.type === NAV_TYPES.PLAYER_DETAIL ||
              navigation.current?.type === NAV_TYPES.TOURNAMENT_DETAIL) && (
              <NavigationRenderer
                navObject={navigation.current}
                onNavigate={handleNavigate}
                onPlayerUpdated={updatePlayer}
                onTournamentUpdate={handleTournamentUpdate}
                onTournamentDelete={handleTournamentDelete}
                isAdmin={isAdmin}
                handleImportClick={handleImportClick}
                handleImportTournamentResults={handleImportTournamentResults}
                players={players}
                tournaments={tournaments}
                activeOnly={activeOnly}
                setActiveOnly={setActiveOnly}
                reloadPlayers={reloadPlayers}
                reloadTournaments={reloadTournaments}
              />
            )}
          </>
        ) : (
          /* Mobile layout - show current navigation object */
          <NavigationRenderer
            navObject={navigation.current}
            onNavigate={handleNavigate}
            onPlayerUpdated={updatePlayer}
            onTournamentUpdate={handleTournamentUpdate}
            onTournamentDelete={handleTournamentDelete}
            isAdmin={isAdmin}
            handleImportClick={handleImportClick}
            handleImportTournamentResults={handleImportTournamentResults}
            players={players}
            tournaments={tournaments}
            activeOnly={activeOnly}
            setActiveOnly={setActiveOnly}
            reloadPlayers={reloadPlayers}
            reloadTournaments={reloadTournaments}
          />
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
    </PlayerListProvider>
  );
}

export default MainWindow;
