import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';

function TournamentDetails({ tournament }) {
  if (!tournament) return null;
  return (
    <Card sx={{ m: 2 }}>
      <CardContent>
        <Typography variant="h5">{tournament.name}</Typography>
        <Typography variant="subtitle1">Date: {tournament.date}</Typography>
        <Typography variant="body2">Location: {tournament.location}</Typography>
        {/* Add more tournament details as needed */}
      </CardContent>
    </Card>
  );
}

export default TournamentDetails;
