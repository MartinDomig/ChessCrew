import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch } from './api';

const PlayerListContext = createContext();

export function usePlayerList() {
  return useContext(PlayerListContext);
}

export function PlayerListProvider({ children }) {
  const [players, setPlayers] = useState([]);
  const [activeOnly, setActiveOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [scrollOffset, setScrollOffset] = useState(0);

  const reloadPlayers = () => {
    setLoading(true);
    const param = activeOnly ? '?active=true' : '';
    apiFetch(`/players${param}`)
      .then(data => {
        setPlayers(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  // Update a single player in the cached list
  const updatePlayer = (updatedPlayer) => {
    setPlayers(prev => prev.map(p => p.id === updatedPlayer.id ? updatedPlayer : p));
  };

  useEffect(() => {
    reloadPlayers();
    // eslint-disable-next-line
  }, [activeOnly]);

  return (
    <PlayerListContext.Provider value={{ players, reloadPlayers, updatePlayer, activeOnly, setActiveOnly, loading, scrollOffset, setScrollOffset }}>
      {children}
    </PlayerListContext.Provider>
  );
}
