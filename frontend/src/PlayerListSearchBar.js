import React, { useState, useEffect } from 'react';
import { usePlayerList } from './PlayerListContext';
import { Box, Autocomplete, TextField } from '@mui/material';
import { apiFetch } from './api';

function PlayerListSearchBar() {
  const { 
    searchTags,
    setSearchTags,
    inputValue,
    setInputValue
  } = usePlayerList();
  const [allTags, setAllTags] = useState([]);
  const [debouncedInput, setDebouncedInput] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedInput(inputValue || '');
    }, 300);
    return () => clearTimeout(handler);
  }, [inputValue]);

  useEffect(() => {
    apiFetch(`/tags`)
      .then(setAllTags);
  }, []);

  const handleAutocompleteChange = (event, value) => {
    setSearchTags(value);
  };

  const handleInputChange = (event, value) => {
    setInputValue(typeof value === 'string' ? value : '');
  };

  return (
    <Box sx={{ px: 0, py: 0.5, background: '#fafafa', borderBottom: '1px solid #eee' }}>
      <Autocomplete
        multiple
        freeSolo
        options={Array.isArray(allTags) ? allTags.map(tag => tag.name) : []}
        value={searchTags}
        inputValue={inputValue}
        onChange={handleAutocompleteChange}
        onInputChange={handleInputChange}
        renderInput={params => (
          <TextField
            {...params}
            variant="outlined"
            placeholder="Spieler suchen..."
            autoFocus
          />
        )}
        sx={{ width: '100%', '& .MuiAutocomplete-root': { margin: 0 } }}
      />
    </Box>
  );
}

export default PlayerListSearchBar;