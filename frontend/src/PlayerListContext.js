import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch } from './api';

const PlayerListContext = createContext();

export function usePlayerList() {
  return useContext(PlayerListContext);
}

export function PlayerListProvider({ children }) {
  const [players, setPlayers] = useState([]);
  const [activeOnly, setActiveOnly] = useState(false);
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

  useEffect(() => {
    reloadPlayers();
    // eslint-disable-next-line
  }, [activeOnly]);

  return (
    <PlayerListContext.Provider value={{ players, reloadPlayers, activeOnly, setActiveOnly, loading, scrollOffset, setScrollOffset }}>
      {children}
    </PlayerListContext.Provider>
  );
}
