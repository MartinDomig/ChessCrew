import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CircularProgress from '@mui/material/CircularProgress';
import DeleteIcon from '@mui/icons-material/Delete';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import React, {useEffect, useState} from 'react';

import {apiFetch} from './api';

function TournamentDetails({tournament, onPlayerClick, onDelete}) {
  const [players, setPlayers] = useState([]);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState(null);

  useEffect(() => {
    if (!tournament?.id) return;

    const fetchTournamentData = async () => {
      setLoading(true);
      setError('');
      try {
        const [playersData, gamesData] = await Promise.all([
          apiFetch(`/tournaments/${tournament.id}/players`),
          apiFetch(`/tournaments/${tournament.id}/games`)
        ]);
        setPlayers(playersData || []);
        setGames(gamesData || []);
      } catch (err) {
        setError('Fehler beim Laden der Turnierdaten');
        console.error('Error fetching tournament data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTournamentData();
  }, [tournament?.id]);

  if (!tournament) return null;

  // Format date to show only date part (YYYY-MM-DD)
  let dateStr = '';
  if (tournament.date) {
      const d = new Date(tournament.date);
      if (!isNaN(d)) {
        dateStr = d.toLocaleDateString();
      } else {
        dateStr = tournament.date.split('T')[0];
      }
  }

  // Sort tournament players by rank
  const sortedPlayers = players.sort((a, b) => {
      if (a.rank && b.rank) return a.rank - b.rank;
      if (a.rank) return -1;
      if (b.rank) return 1;
      return (b.points || 0) - (a.points || 0);  // Sort by points if no rank
  });

  const handlePlayerClick = (tp) => {
      if (!tp.player_id) return;
      // fetch player details and use parent navigation
      apiFetch(`/players/${tp.player_id}`)
          .then(data => {
            if (onPlayerClick) {
              onPlayerClick(data, tournament);
            } else {
              // Fallback for backwards compatibility
              setSelectedPlayer(data);
            }
          })
          .catch(err => {
            console.error('Error fetching player details:', err);
          });
  };

  const handleDelete = async () => {
    if (window.confirm('Sind Sie sicher, dass Sie dieses Turnier löschen möchten?')) {
      try {
        await apiFetch(`/tournaments/${tournament.id}`, { method: 'DELETE' });
        if (onDelete) {
          onDelete(tournament.id);
        }
      } catch (err) {
        alert(err.message || 'Fehler beim Löschen des Turniers');
        console.error('Error deleting tournament:', err);
      }
    }
  };

  return (
    <Box sx={{
      m: 2, maxWidth: '100%' }}>
      <Card sx={{
      mb: 2 }}>
        <CardContent>
          <Typography variant='h5'>{tournament.name}</Typography>
          <Typography variant="subtitle1">Datum: {dateStr}</Typography>
          <Typography variant='body2'>Ort: {tournament.location}</Typography>
          <Typography variant='body2'>Teilnehmer: {sortedPlayers.length}</Typography>
        </CardContent>
      </Card>

      {loading && (
        <Box sx={{
      display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography color="error">{error}</Typography>
          </CardContent>
        </Card>
      )}

      {!loading && sortedPlayers.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant='h6' sx={{
        mb: 2 }}>
              Endergebnis
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table size="small" stickyHeader sx={{ '& .MuiTableCell-root': { padding: '4px 8px' } }}>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>#</TableCell>
                    <TableCell sx={{
        fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Name</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Pt</TableCell>
                    <TableCell align='right' sx={{
        fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Tie</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedPlayers.map((tp, index) => {
                    const displayName = tp.player 
                      ? `${tp.player.first_name} ${tp.player.last_name}`
                      : tp.name || 'Unbekannt';
                    
                    // Format tiebreakers as (tie1/tie2) or just (tie1) if no tie2 or tie2 is zero or same as tie1
      let tieDisplay = '-';
          if (tp.tiebreak1 !== null && tp.tiebreak1 !== undefined) {
            tieDisplay = `(${tp.tiebreak1}`;
            if (tp.tiebreak2 !== null && tp.tiebreak2 !== undefined &&
                tp.tiebreak2 !== 0 && tp.tiebreak2 !== tp.tiebreak1) {
              tieDisplay += `/${tp.tiebreak2}`;
            }
            tieDisplay += ')';
          }

      const isClickable = tp.player_id;

          return (
              <TableRow key = {tp.id || index} sx = {
                {
                  '&:hover': isClickable ?
                      {backgroundColor: '#f0f0f0', cursor: 'pointer'} :
                      {}
                }
              }>
                <TableCell>{tp.rank || (index + 1)}</TableCell>
                        <TableCell 
                          onClick={() => handlePlayerClick(tp)}
                          sx={{ 
                            color: isClickable ? 'primary.main' : 'inherit',
                            cursor: isClickable ? 'pointer' : 'default',
                            '&:hover': isClickable ? { textDecoration: 'underline' } : {}
                          }}
                        >
                          {displayName}
                        </TableCell>
                <TableCell align = 'right'>{
                  tp.points !== null ? tp.points : '-'}</TableCell>
                        <TableCell align="right">{tieDisplay}</TableCell>
              </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
              </CardContent>
        </Card>)}

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" color="error" onClick={handleDelete}>
          <DeleteIcon sx={{ mr: 1 }} />
          Turnier löschen
        </Button>
      </Box>
    </Box>
  );
}

export default TournamentDetails;
