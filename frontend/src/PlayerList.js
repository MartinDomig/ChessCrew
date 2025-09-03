import React, { useRef, useEffect, useState } from 'react';
import { usePlayerList } from './PlayerListContext';
import { FixedSizeList as List } from 'react-window';
import PlayerCard from './PlayerCard';
import { Box, Typography } from '@mui/material';
import { apiFetch } from './api';

export default function PlayerList({ players, onPlayerClick, onStatusChange, showSearchBar = true }) {
  const { 
    scrollOffset, 
    setScrollOffset,
    filteredPlayers,
    searchTags,
    setSearchTags,
    inputValue,
    setInputValue
  } = usePlayerList();

  const [containerHeight, setContainerHeight] = useState(400); // Default height
  const containerRef = useRef(null);

  // Update height when component mounts or container resizes
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        const height = containerRef.current.clientHeight;
        if (height > 0) {
          setContainerHeight(height);
        }
      }
    };

    updateHeight();
    
    // Set up resize observer to handle dynamic height changes
    const resizeObserver = new ResizeObserver(updateHeight);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      if (containerRef.current) {
        resizeObserver.unobserve(containerRef.current);
      }
    };
  }, []);

  const handleTagClick = (tag) => {
    setSearchTags(tags => {
      const currentTags = Array.isArray(tags) ? tags : [];
      // Check if tag is already in the list
      if (currentTags.includes(tag.name)) {
        return currentTags; // No change needed
      }
      return [...currentTags, tag.name];
    });
  };

  const handleCategoryClick = (category) => {
    // add category to input value if it is not already there
    const currentValue = typeof inputValue === 'string' ? inputValue : '';
    if (!currentValue.includes(category)) {
      setInputValue(value => {
        const current = typeof value === 'string' ? value : '';
        return `${current} ${category}`.trim();
      });
    }
  };

  // Ref for the List component
  const listRef = useRef(null);

  // Handler to preserve scroll position in context
  const handlePlayerClick = (player) => {
    if (listRef.current) {
      setScrollOffset(listRef.current.state.scrollOffset);
    }
    onPlayerClick(player);
  };

  // Restore scroll position when list is shown
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo(scrollOffset);
    }
  }, [listRef, scrollOffset, players.length]);

  return (
    <Box ref={containerRef} sx={{ width: '100%', height: '100%' }}>
      {filteredPlayers.length === 0 ? (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          minHeight: '200px'
        }}>
          <Typography variant="body1" color="text.secondary">
            No players found
          </Typography>
        </Box>
      ) : (
        <List
          ref={listRef}
          height={containerHeight}
          itemCount={filteredPlayers.length}
          itemSize={107}
          width={'100%'}
          style={{}}
        >
          {({ index, style }) => {
            const player = filteredPlayers[index];
            return (
              <Box key={player.id} sx={{ ...style, cursor: 'pointer' }} onClick={() => handlePlayerClick(player)}>
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
    </Box>
  );
}
