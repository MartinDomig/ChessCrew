import React, { useState, useEffect } from 'react';
import { useTournamentList } from './TournamentListContext';
import { Box, TextField } from '@mui/material';

function TournamentListSearchBar() {
  const {
    searchInput,
    setSearchInput
  } = useTournamentList();

  const [debouncedInput, setDebouncedInput] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedInput(searchInput || '');
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput]);

  const handleInputChange = (event) => {
    setSearchInput(event.target.value);
  };

  return (
    <Box sx={{ px: 0, py: 0.5, background: '#fafafa', borderBottom: '1px solid #eee' }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Turniere suchen..."
        value={searchInput}
        onChange={handleInputChange}
        autoFocus
        size="small"
      />
    </Box>
  );
}

export default TournamentListSearchBar;