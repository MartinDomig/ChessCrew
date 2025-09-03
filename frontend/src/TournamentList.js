import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React from 'react';

function TournamentList({tournaments, onTournamentClick}) {
  // Sort tournaments: date descending, then name ascending
  const sortedTournaments = [...tournaments].sort((a, b) => {
    // Parse dates for comparison
    const dateA = a.date ? new Date(a.date) : new Date(0);
    const dateB = b.date ? new Date(b.date) : new Date(0);
    
    // First sort by date descending (newest first)
    const dateComparison = dateB.getTime() - dateA.getTime();
    if (dateComparison !== 0) {
      return dateComparison;
    }
    
    // If dates are equal, sort by name ascending (A-Z)
    const nameA = (a.name || '').toLowerCase();
    const nameB = (b.name || '').toLowerCase();
    return nameA.localeCompare(nameB);
  });

  return (
    <List sx={{ pl: 0, pr: 0 }}>
      {sortedTournaments.map((tournament) => {
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
