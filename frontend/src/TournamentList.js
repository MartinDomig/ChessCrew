import React from 'react';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';

function TournamentList({ tournaments, onTournamentClick }) {
  return (
    <List>
      {tournaments.map((tournament) => (
        <ListItem key={tournament.id} disablePadding>
          <ListItemButton onClick={() => onTournamentClick(tournament)}>
            <ListItemText primary={tournament.name} secondary={tournament.date} />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
}

export default TournamentList;
