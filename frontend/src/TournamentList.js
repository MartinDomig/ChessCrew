import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React from 'react';
import TournamentTypeIndicator from './TournamentTypeIndicator';
import { Box, Typography } from '@mui/material';

function TournamentList({tournaments, onTournamentClick}) {
  // Use the filtered tournaments passed as props (from context)
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
      return (
          <Box 
            key={tournament.id} 
            onClick={() => onTournamentClick(tournament)}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              py: 1,
              ml: 2,
              borderBottom: '1px solid',
              borderColor: 'divider',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover'
              }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <TournamentTypeIndicator tournament={tournament} size="small" />
              <Typography variant="body2" sx={{ ml: 1 }}>{tournament.name}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{secondary}</Typography>
          </Box>
        );
      })}
    </List>);
}

export default TournamentList;
