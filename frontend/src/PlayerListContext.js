import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { apiFetch } from './api';

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
};

// Initial state
const initialState = {
  players: [],
  loading: false,
  activeOnly: true,
  scrollOffset: 0,
  searchTags: [],
  inputValue: '',
};

// Reducer function
function playerListReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case ACTIONS.SET_PLAYERS:
      return { ...state, players: action.payload, loading: false };
    case ACTIONS.UPDATE_PLAYER:
      return {
        ...state,
        players: state.players.map(p =>
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

  const reloadPlayers = () => {
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    const param = state.activeOnly ? '?active=true' : '';
    apiFetch(`/players${param}`)
      .then(data => dispatch({ type: ACTIONS.SET_PLAYERS, payload: data }))
      .catch(() => dispatch({ type: ACTIONS.SET_LOADING, payload: false }));
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
    const currentDebouncedInput = debouncedInput || '';
    const stringTerms = currentDebouncedInput.split(/\s+/).filter(Boolean);
    
    return state.players.filter(player => {
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
    players: state.players,
    filteredPlayers,
    loading: state.loading,
    activeOnly: state.activeOnly,
    scrollOffset: state.scrollOffset,
    searchTags: state.searchTags,
    inputValue: typeof state.inputValue === 'string' ? state.inputValue : '',
    
    // Actions
    reloadPlayers,
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
