import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import React from 'react';

const sortPlayersByRank = (players) => {
  return [...players].sort((a, b) => {
    if (a.rank && b.rank) return a.rank - b.rank;
    if (a.rank) return -1;
    if (b.rank) return 1;
    return (b.points || 0) - (a.points || 0);
  });
};

const formatTiebreakers = (tiebreak1, tiebreak2) => {
  if (tiebreak1 === null || tiebreak1 === undefined) return '-';

  let display = `(${tiebreak1}`;
  if (tiebreak2 !== null && tiebreak2 !== undefined &&
      tiebreak2 !== 0 && tiebreak2 !== tiebreak1) {
    display += `/${tiebreak2}`;
  }
  display += ')';
  return display;
};

function PlayerRow({ player, index, onPlayerClick }) {
  const displayName = player.player
    ? `${player.player.first_name} ${player.player.last_name}`
    : player.name || 'Unbekannt';

  const tieDisplay = formatTiebreakers(player.tiebreak1, player.tiebreak2);
  const isClickable = player.player_id;

  const handleClick = () => {
    if (isClickable) {
      onPlayerClick(player);
    }
  };

  return (
    <TableRow
      sx={{
        '&:hover': isClickable ? { backgroundColor: '#f0f0f0', cursor: 'pointer' } : {}
      }}
    >
      <TableCell>{player.rank || (index + 1)}</TableCell>
      <TableCell
        onClick={handleClick}
        sx={{
          color: isClickable ? 'primary.main' : 'inherit',
          cursor: isClickable ? 'pointer' : 'default',
          '&:hover': isClickable ? { textDecoration: 'underline' } : {}
        }}
      >
        {displayName}
      </TableCell>
      <TableCell align="right">{player.points !== null ? player.points : '-'}</TableCell>
      <TableCell align="right">{tieDisplay}</TableCell>
    </TableRow>
  );
}

function TournamentResults({ players, onPlayerClick }) {
  const sortedPlayers = sortPlayersByRank(players);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Endergebnis
        </Typography>
        <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
          <Table size="small" stickyHeader sx={{ '& .MuiTableCell-root': { padding: '4px 8px' } }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>#</TableCell>
                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Name</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Pt</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Tie</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedPlayers.map((player, index) => (
                <PlayerRow
                  key={player.id || index}
                  player={player}
                  index={index}
                  onPlayerClick={onPlayerClick}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}

export default TournamentResults;
