import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';

export function UpdateHelp() {
  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle2">
          💡 Wie stelle ich sicher, dass ich die neueste Version habe?
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box>
          <Typography variant="body2" gutterBottom>
            Es gibt mehrere Möglichkeiten, die App auf dem neuesten Stand zu halten:
          </Typography>
          
          <List dense>
            <ListItem>
              <ListItemText
                primary="🔄 Automatische Benachrichtigungen"
                secondary="Die App prüft alle 5 Minuten automatisch nach Updates und zeigt eine Benachrichtigung an."
              />
            </ListItem>
            
            <ListItem>
              <ListItemText
                primary="⚡ Manuell prüfen"
                secondary="Menü öffnen → 'Nach Updates suchen' → Updates werden sofort geprüft"
              />
            </ListItem>
            
            <ListItem>
              <ListItemText
                primary="🔄 Browser-Refresh"
                secondary="Seite neu laden (Pull-to-refresh oder Strg+F5)"
              />
            </ListItem>
            
            <ListItem>
              <ListItemText
                primary="📱 App neu starten"
                secondary="Auf mobilen Geräten: App schließen und neu öffnen"
              />
            </ListItem>
          </List>
          
          <Typography variant="caption" color="text.secondary">
            Die Versionsnummer finden Sie im Hauptmenü.
          </Typography>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
