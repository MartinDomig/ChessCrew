import EmailIcon from '@mui/icons-material/Email';
import FilterListIcon from '@mui/icons-material/FilterList';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import RefreshIcon from '@mui/icons-material/Refresh';
import SportsScoreIcon from '@mui/icons-material/SportsScore';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';
import React, {useState, useRef} from 'react';
import { VersionInfo } from './VersionInfo';

function BurgerMenu({onLogout}) {
  const [anchorEl, setAnchorEl] = useState(null);
  const versionInfoRef = useRef(null);
  const handleMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogoutClick = () => {
    onLogout();
    handleMenuClose();
  };

  const handleCheckForUpdates = async () => {
    handleMenuClose();
    
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          // Force check for updates
          await registration.update();
          
          // Refresh version info to show latest version
          if (versionInfoRef.current) {
            versionInfoRef.current.refresh();
          }
          
          // Check if there's a waiting service worker
          if (registration.waiting) {
            // There's an update available, let the user know
            if (window.confirm('Eine neue Version ist verfügbar! Möchten Sie jetzt aktualisieren?')) {
              registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
          } else {
            // No update available
            alert('Sie haben bereits die neueste Version!');
          }
        }
      } catch (error) {
        console.error('Failed to check for updates:', error);
        // Fallback: just reload the page
        if (window.confirm('Nach Updates suchen... Seite neu laden?')) {
          window.location.reload();
        }
      }
    } else {
      // Service worker not supported, just reload
      if (window.confirm('Nach Updates suchen... Seite neu laden?')) {
        window.location.reload();
      }
    }
  };

  return (
      <><IconButton edge = 'end' color = 'inherit' sx =
         {
           { ml: 2 }
         } onClick = {handleMenuOpen}><MenuIcon />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={handleCheckForUpdates}>
          <ListItemIcon>
            <RefreshIcon />
          </ListItemIcon>
          Nach Updates suchen
        </MenuItem>
        <MenuItem onClick={handleLogoutClick}>
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          Logout
        </MenuItem>
        <VersionInfo ref={versionInfoRef} />
      </Menu>
    </>);
}

export default BurgerMenu;
