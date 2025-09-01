import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import React from 'react';

function TournamentDetails({tournament}) {
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
  return (
    <Card sx={{
    m: 2 }}>
      <CardContent>
        <Typography variant='h5'>{tournament.name}</Typography>
        <Typography variant="subtitle1">Datum: {dateStr}</Typography>
        <Typography variant='body2'>Ort: {tournament.location}</Typography>
        {/* Add more tournament details as needed */}
      </CardContent>
    </Card>
  );
}

export default TournamentDetails;
