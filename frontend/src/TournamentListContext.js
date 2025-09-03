import React, {createContext, useContext, useEffect, useState} from 'react';

import {apiFetch} from './api';
import { extractArrayWithMetadata } from './arrayUtils';

const TournamentListContext = createContext();

export function TournamentListProvider({children}) {
  const [tournaments, setTournaments] = useState([]);
  const [hasStaleData, setHasStaleData] = useState(false);

  const reloadTournaments = async () => {
    const data = await apiFetch('/tournaments');
    
    // Extract array and metadata using utility function
    const { array: tournamentsArray, isStale } = extractArrayWithMetadata(data, 'tournaments');
    
    setTournaments(tournamentsArray);
    setHasStaleData(isStale);
  };

  useEffect(() => {
    reloadTournaments();
  }, []);

  return (
    <TournamentListContext.Provider value={{
    tournaments, reloadTournaments, hasStaleData }}>
      {children}
    </TournamentListContext.Provider>
  );
}

export function useTournamentList() {
  return useContext(TournamentListContext);
}
