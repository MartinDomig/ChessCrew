import React, {createContext, useContext, useEffect, useState} from 'react';

import {apiFetch} from './api';

const TournamentListContext = createContext();

export function TournamentListProvider({children}) {
  const [tournaments, setTournaments] = useState([]);
  const [hasStaleData, setHasStaleData] = useState(false);

  const reloadTournaments = async () => {
    const data = await apiFetch('/tournaments');
    
    // Handle cache metadata - arrays can have metadata as properties
    let tournamentsArray = [];
    let isStale = false;
    
    if (data) {
      // Check for stale metadata (can be on arrays or objects)
      isStale = data._isStale === true;
      
      // Extract the actual array data
      if (Array.isArray(data)) {
        // Data is already an array, use it directly
        tournamentsArray = data.slice(); // Create a copy to avoid mutations
      } else if (data && typeof data === 'object') {
        // Check if it's an array-like object with numeric keys (from cache deserialization)
        const keys = Object.keys(data).filter(key => key !== '_isStale' && key !== '_cacheAge');
        const isArrayLike = keys.length > 0 && keys.every(key => /^\d+$/.test(key));
        
        if (isArrayLike) {
          // Convert array-like object to proper array
          const maxIndex = Math.max(...keys.map(k => parseInt(k, 10)));
          tournamentsArray = Array.from({ length: maxIndex + 1 }, (_, i) => data[i]).filter(item => item !== undefined);
          console.log('Converted tournaments array-like object to array:', tournamentsArray.length);
        } else if (Array.isArray(data.tournaments)) {
          tournamentsArray = data.tournaments;
        } else if (Array.isArray(data.data)) {
          tournamentsArray = data.data;
        } else {
          // Try to extract from destructured cache metadata
          const { _isStale, _cacheAge, ...rest } = data;
          if (Array.isArray(rest)) {
            tournamentsArray = rest;
          } else {
            console.warn('Could not extract tournaments array from data:', data);
            tournamentsArray = [];
          }
        }
      }
    }
    
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
