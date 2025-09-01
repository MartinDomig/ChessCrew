import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React from 'react';

function TournamentList({tournaments, onTournamentClick}) {
  return (
    <List>
      {tournaments.map((tournament) => {
      let dateStr = '';
      if (tournament.date) {
        const d = new Date(tournament.date);
        if (!isNaN(d)) {
          dateStr = d.toLocaleDateString();
        } else {
          dateStr = tournament.date.split('T')[0];
        }
      }
      const secondary =
          [tournament.location, dateStr].filter(Boolean).join(' • ');
      return (<ListItem key = {tournament.id} disablePadding>
              <ListItemButton onClick = {() => onTournamentClick(tournament)}>
              <ListItemText primary = {tournament.name} secondary =
               {
                 secondary
               } />
            </ListItemButton>
              </ListItem>
        );
      })}
    </List>);
}

export default TournamentList;
