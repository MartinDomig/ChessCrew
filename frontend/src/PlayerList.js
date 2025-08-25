import React, { useState, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import PlayerCard from './PlayerCard';
import { Box, Paper, Chip, Autocomplete, TextField } from '@mui/material';
import TagChip from './TagChip';

export default function PlayerList({ players, onPlayerClick, onStatusChange }) {
  const [searchTags, setSearchTags] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [debouncedInput, setDebouncedInput] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedInput(inputValue);
    }, 300);
    return () => clearTimeout(handler);
  }, [inputValue]);

  const handleTagClick = (tag) => {
    if (!searchTags.includes(tag.name)) {
      setSearchTags(tags => [...tags, tag.name]);
    }
  };

  const handleCategoryClick = (category) => {
    // add category to input value if it is not already there
    if (!inputValue.includes(category)) {
      setInputValue(value => `${value} ${category}`.trim());
    }
  };

  const handleAutocompleteChange = (event, value) => {
    console.log('Autocomplete changed:', value);
    setSearchTags(value);
  };

  const handleInputChange = (event, value) => {
    setInputValue(value);
  };

  // Separate tag and string search logic
  const stringTerms = debouncedInput.split(/\s+/).filter(Boolean);
  const filteredPlayers = players.filter(player => {
    // AND logic for tags: player must have all selected tags
    if (searchTags.length > 0) {
      const playerTagNames = (player.tags || []).map(t => t.name);
      if (!searchTags.every(tag => playerTagNames.includes(tag))) {
        return false;
      }
    }
    // OR logic for string search (name/category)
    const name = `${player.first_name} ${player.last_name}`.toLowerCase();
    const kat = (player.kat || "").toLowerCase();
    return stringTerms.length === 0 || stringTerms.some(term => name.includes(term.toLowerCase()) || kat.includes(term.toLowerCase()));
  });

  return (
    <>
      <Box sx={{ px: 2, py: 1, background: '#fafafa', borderBottom: '1px solid #eee' }}>
        <Autocomplete
          multiple
          freeSolo
          options={[]}
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
              slotProps={{
                input: {
                    startAdornment: searchTags.map((option, index) => (
                      <TagChip
                        tag={{ name: option }}
                        size="small"
                        key={option}
                        onClick={() => {
                          setSearchTags(tags => tags.filter((t, i) => i !== index));
                        }}
                        sx={{ mr: 0.5 }}
                      />
                    )),
                },
              }}
            />
          )}
          sx={{ width: '100%' }}
        />
      </Box>
      {filteredPlayers.length === 0 ? null : (
        <List
          height={window.innerHeight - 128 > 300 ? window.innerHeight - 128 : 300}
          itemCount={filteredPlayers.length}
          itemSize={180}
          width={"100%"}
          style={{ maxWidth: 500, margin: "0 auto" }}
        >
          {({ index, style }) => {
            const player = filteredPlayers[index];
            return (
              <Box key={player.id} sx={{ ...style, cursor: 'pointer' }} onClick={() => onPlayerClick(player)}>
                <PlayerCard
                  player={player}
                  onStatusChange={isActive => onStatusChange(player.id, isActive)}
                  onTagClick={handleTagClick}
                  onCategoryClick={handleCategoryClick}
                />
              </Box>
            );
          }}
        </List>
      )}
    </>
  );
}
