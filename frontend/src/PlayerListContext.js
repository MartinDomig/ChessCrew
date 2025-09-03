import React, { createContext, useContext, useReducer, useEffect, useState } from 'react';
import { apiFetch, getCacheInfo, preloadCommonData } from './api';
import { extractArrayWithMetadata } from './arrayUtils';

const PlayerListContext = createContext();

// Action types
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_PLAYERS: 'SET_PLAYERS',
  UPDATE_PLAYER: 'UPDATE_PLAYER',
  SET_ACTIVE_ONLY: 'SET_ACTIVE_ONLY',
  SET_SCROLL_OFFSET: 'SET_SCROLL_OFFSET',
  SET_SEARCH_TAGS: 'SET_SEARCH_TAGS',
  SET_INPUT_VALUE: 'SET_INPUT_VALUE',
  SET_HAS_STALE_DATA: 'SET_HAS_STALE_DATA',
};

// Initial state
const initialState = {
  players: [],
  loading: false,
  activeOnly: true,
  scrollOffset: 0,
  searchTags: [],
  inputValue: '',
  hasStaleData: false,
};

// Reducer function
function playerListReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case ACTIONS.SET_PLAYERS:
      // Ensure players is always an array
      const players = Array.isArray(action.payload) ? action.payload : [];
      return { ...state, players, loading: false };
    case ACTIONS.UPDATE_PLAYER:
      // Ensure state.players is an array before mapping
      const currentPlayers = Array.isArray(state.players) ? state.players : [];
      return {
        ...state,
        players: currentPlayers.map(p =>
          p.id === action.payload.id ? action.payload : p
        )
      };
    case ACTIONS.SET_ACTIVE_ONLY:
      return { ...state, activeOnly: action.payload };
    case ACTIONS.SET_SCROLL_OFFSET:
      return { ...state, scrollOffset: action.payload };
    case ACTIONS.SET_SEARCH_TAGS:
      // Ensure payload is always an array
      const tags = Array.isArray(action.payload) ? action.payload : [];
      return { ...state, searchTags: tags };
    case ACTIONS.SET_INPUT_VALUE:
      return { ...state, inputValue: action.payload };
    case ACTIONS.SET_HAS_STALE_DATA:
      return { ...state, hasStaleData: action.payload };
    default:
      return state;
  }
}

export function usePlayerList() {
  const context = useContext(PlayerListContext);
  if (!context) {
    throw new Error('usePlayerList must be used within a PlayerListProvider');
  }
  return context;
}

export function PlayerListProvider({ children }) {
  const [state, dispatch] = useReducer(playerListReducer, initialState);
  const [lastRequestTime, setLastRequestTime] = useState(0);

  const reloadPlayers = async (forceNetwork = false) => {
    // Prevent duplicate requests within 500ms
    const now = Date.now();
    if (!forceNetwork && now - lastRequestTime < 500) {
      console.log('Skipping duplicate request within 500ms');
      return;
    }
    setLastRequestTime(now);
    
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    const param = state.activeOnly ? '?active=true' : '';
    const endpoint = `/players${param}`;
    
    try {
      // For full players list (slow endpoint), check if we have fresh cached data first
      if (!forceNetwork && !state.activeOnly) {
        const cacheInfo = await getCacheInfo();
        const cachedEntry = cacheInfo.entries.find(entry => 
          entry.url.includes('/players') && !entry.url.includes('active=true')
        );
        
        // If we have valid cached data (not expired or stale), skip the network request
        if (cachedEntry && cachedEntry.status === 'valid') {
          console.log('Using cached full players list to avoid slow network request');
        }
      }
      
      const data = await apiFetch(endpoint);
      
      // Extract array and metadata using utility function
      const { array: playersArray, isStale } = extractArrayWithMetadata(data, 'players');
      
      console.log('Processed players data:', { isArray: Array.isArray(playersArray), length: playersArray.length, isStale });
      
      dispatch({ type: ACTIONS.SET_PLAYERS, payload: playersArray });
      dispatch({ type: ACTIONS.SET_HAS_STALE_DATA, payload: isStale });
      
      // Only start background preloading if this is the initial load (not a refresh)
      // and we're online, and we haven't already preloaded
      if (!forceNetwork && navigator.onLine) {
        const currentFilter = state.activeOnly ? 'active' : 'all';
        // Delay preloading to avoid interfering with UI and to prevent double requests
        setTimeout(() => {
          // Only preload if we don't already have cached data for the opposite filter
          getCacheInfo().then(cacheInfo => {
            const oppositeEndpoint = state.activeOnly ? '/players' : '/players?active=true';
            const hasOppositeCache = cacheInfo.entries.some(entry => 
              entry.url.includes(oppositeEndpoint) && entry.status === 'valid'
            );
            
            if (!hasOppositeCache) {
              console.log('Starting background preload for opposite filter');
              preloadCommonData(currentFilter);
            } else {
              console.log('Opposite filter already cached, skipping preload');
            }
          });
        }, 2000); // Increased delay to ensure UI is fully loaded
      }
    } catch (error) {
      console.error('Failed to load players:', error);
      dispatch({ type: ACTIONS.SET_LOADING, payload: false });
    }
  };

  const setInputValue = (value) => {
    if (typeof value === 'function') {
      // Support functional updates like React's useState
      const currentValue = state.inputValue;
      const newValue = value(currentValue);
      dispatch({ type: ACTIONS.SET_INPUT_VALUE, payload: newValue });
    } else {
      dispatch({ type: ACTIONS.SET_INPUT_VALUE, payload: value });
    }
  };

  const forceReloadPlayers = () => {
    return reloadPlayers(true); // Force network request
  };

  const updatePlayer = (updatedPlayer) => {
    dispatch({ type: ACTIONS.UPDATE_PLAYER, payload: updatedPlayer });
  };

  const setActiveOnly = (activeOnly) => {
    dispatch({ type: ACTIONS.SET_ACTIVE_ONLY, payload: activeOnly });
  };

  const setScrollOffset = (offset) => {
    dispatch({ type: ACTIONS.SET_SCROLL_OFFSET, payload: offset });
  };

  const setSearchTags = (tagsOrUpdater) => {
    if (typeof tagsOrUpdater === 'function') {
      // Support functional updates like React's setState
      const currentTags = Array.isArray(state.searchTags) ? state.searchTags : [];
      const newTags = tagsOrUpdater(currentTags);
      const safeNewTags = Array.isArray(newTags) ? newTags : [];
      dispatch({ type: ACTIONS.SET_SEARCH_TAGS, payload: safeNewTags });
    } else {
      const safeTags = Array.isArray(tagsOrUpdater) ? tagsOrUpdater : [];
      dispatch({ type: ACTIONS.SET_SEARCH_TAGS, payload: safeTags });
    }
  };

  // Debounce input value for search
  const [debouncedInput, setDebouncedInput] = React.useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedInput(state.inputValue || '');
    }, 300);
    return () => clearTimeout(handler);
  }, [state.inputValue]);

  // Filtering logic
  const filteredPlayers = React.useMemo(() => {
    // Ensure players is always an array with debugging
    const playersArray = Array.isArray(state.players) ? state.players : [];
    
    if (!Array.isArray(state.players)) {
      console.error('state.players is not an array in useMemo:', {
        type: typeof state.players,
        value: state.players,
        keys: state.players ? Object.keys(state.players) : 'null'
      });
    }
    
    // Ensure searchTags is always an array
    const searchTagsArray = Array.isArray(state.searchTags) ? state.searchTags : [];
    
    if (!Array.isArray(state.searchTags)) {
      console.error('state.searchTags is not an array in useMemo:', {
        type: typeof state.searchTags,
        value: state.searchTags
      });
    }
    
    const currentDebouncedInput = debouncedInput || '';
    const stringTerms = currentDebouncedInput.split(/\s+/).filter(Boolean);
    
    return playersArray.filter(player => {
      // AND logic for tags: player must have all selected tags
      if (searchTagsArray.length > 0) {
        const playerTagNames = (player.tags || []).map(t => t.name);
        if (!searchTagsArray.every(tag => playerTagNames.includes(tag))) {
          return false;
        }
      }
      // OR logic for string search
      const name = `${player.first_name} ${player.last_name}`.toLowerCase();
      const kat = (player.kat || "").toLowerCase();
      const pnr = String(player.p_number);
      return stringTerms.length === 0 || stringTerms.some(term => name.includes(term.toLowerCase()) || kat.includes(term.toLowerCase()) || pnr.startsWith(term.toLowerCase()));
    });
  }, [state.players, state.searchTags, debouncedInput]);

  useEffect(() => {
    reloadPlayers();
    // eslint-disable-next-line
  }, [state.activeOnly]);

  const value = {
    // State
    players: Array.isArray(state.players) ? state.players : [],
    filteredPlayers,
    loading: state.loading,
    activeOnly: state.activeOnly,
    scrollOffset: state.scrollOffset,
    searchTags: Array.isArray(state.searchTags) ? state.searchTags : [],
    inputValue: typeof state.inputValue === 'string' ? state.inputValue : '',
    hasStaleData: state.hasStaleData,
    
    // Actions
    reloadPlayers,
    forceReloadPlayers,
    updatePlayer,
    setActiveOnly,
    setScrollOffset,
    setSearchTags,
    setInputValue,
  };

  return (
    <PlayerListContext.Provider value={value}>
      {children}
    </PlayerListContext.Provider>
  );
}
