import React, { useState } from 'react';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ImportExportIcon from '@mui/icons-material/ImportExport';
import FilterListIcon from '@mui/icons-material/FilterList';
import Switch from '@mui/material/Switch';
import LogoutIcon from '@mui/icons-material/Logout';
import Box from '@mui/material/Box';
import EmailIcon from '@mui/icons-material/Email';

function BurgerMenu({ isAdmin, onImportClick, showActiveOnly, onShowActiveChange, onLogout, onExportEmail }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleImport = () => {
    onImportClick();
    handleMenuClose();
  };
  
  const handleShowActiveChange = (_, checked) => {
    if (onShowActiveChange) onShowActiveChange(checked);
    handleMenuClose();
  };

  const handleLogoutClick = () => {
    onLogout();
    handleMenuClose();
  };

  const handleExportEmail = () => {
    if (onExportEmail) onExportEmail();
    handleMenuClose();
  };

  return (
    <>
      <IconButton edge="end" color="inherit" aria-label="menu" sx={{ ml: 2 }} onClick={handleMenuOpen}>
        <MenuIcon />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem disabled={!isAdmin} onClick={handleImport}>
          <ListItemIcon>
            <ImportExportIcon />
          </ListItemIcon>
          Import Meldekartei
        </MenuItem>
        <MenuItem onClick={handleExportEmail}>
          <ListItemIcon>
            <EmailIcon />
          </ListItemIcon>
          Export E-Mail Liste
        </MenuItem>
        <MenuItem>
          <ListItemIcon>
            <FilterListIcon />
          </ListItemIcon>
          <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Nur aktive Spieler anzeigen
            <Switch
              edge="end"
              checked={showActiveOnly}
              onChange={handleShowActiveChange}
              color="primary"
            />
          </Box>
        </MenuItem>
        <MenuItem onClick={handleLogoutClick}>
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </>
  );
}

export default BurgerMenu;
