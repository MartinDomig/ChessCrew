import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { apiFetch, getCacheInfo } from './api';

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
      return { ...state, searchTags: action.payload };
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

  const reloadPlayers = async (forceNetwork = false) => {
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
      
      // Simplify cache metadata handling
      let playersArray = [];
      let isStale = false;
      
      if (data) {
        // Check for stale metadata (can be on arrays or objects)
        isStale = data._isStale === true;
        
        // Extract the actual array data
        if (Array.isArray(data)) {
          // Data is already an array, use it directly
          playersArray = data.slice(); // Create a copy to avoid mutations
        } else if (data && typeof data === 'object') {
          // Check if it's an array-like object with numeric keys (from cache deserialization)
          const keys = Object.keys(data).filter(key => key !== '_isStale' && key !== '_cacheAge');
          const isArrayLike = keys.length > 0 && keys.every(key => /^\d+$/.test(key));
          
          if (isArrayLike) {
            // Convert array-like object to proper array
            const maxIndex = Math.max(...keys.map(k => parseInt(k, 10)));
            playersArray = Array.from({ length: maxIndex + 1 }, (_, i) => data[i]).filter(item => item !== undefined);
            console.log('Converted array-like object to array:', playersArray.length);
          } else if (Array.isArray(data.players)) {
            playersArray = data.players;
          } else if (Array.isArray(data.data)) {
            playersArray = data.data;
          } else {
            // Try to extract from destructured cache metadata
            const { _isStale, _cacheAge, ...rest } = data;
            if (Array.isArray(rest)) {
              playersArray = rest;
            } else {
              console.warn('Could not extract array from data:', data);
              playersArray = [];
            }
          }
        }
      }
      
      console.log('Processed players data:', { isArray: Array.isArray(playersArray), length: playersArray.length, isStale });
      
      dispatch({ type: ACTIONS.SET_PLAYERS, payload: playersArray });
      dispatch({ type: ACTIONS.SET_HAS_STALE_DATA, payload: isStale });
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

  const setSearchTags = (tags) => {
    dispatch({ type: ACTIONS.SET_SEARCH_TAGS, payload: tags });
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
    
    const currentDebouncedInput = debouncedInput || '';
    const stringTerms = currentDebouncedInput.split(/\s+/).filter(Boolean);
    
    return playersArray.filter(player => {
      // AND logic for tags: player must have all selected tags
      if (state.searchTags.length > 0) {
        const playerTagNames = (player.tags || []).map(t => t.name);
        if (!state.searchTags.every(tag => playerTagNames.includes(tag))) {
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
    searchTags: state.searchTags,
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
