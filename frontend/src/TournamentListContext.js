import React, {createContext, useContext, useEffect, useState} from 'react';

import {apiFetch} from './api';

const TournamentListContext = createContext();

export function TournamentListProvider({children}) {
  const [tournaments, setTournaments] = useState([]);

  const reloadTournaments = async () => {
    const data = await apiFetch('/tournaments');
    setTournaments(data);
  };

  useEffect(() => {
    reloadTournaments();
  }, []);

  return (
    <TournamentListContext.Provider value={{
    tournaments, reloadTournaments }}>
      {children}
    </TournamentListContext.Provider>
  );
}

export function useTournamentList() {
  return useContext(TournamentListContext);
}
