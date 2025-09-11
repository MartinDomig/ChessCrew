import React, {createContext, useContext, useEffect, useState, useMemo} from 'react';

import {apiFetch} from './api';
import { extractArrayWithMetadata } from './arrayUtils';

const TournamentListContext = createContext();

export function TournamentListProvider({children}) {
  const [tournaments, setTournaments] = useState([]);
  const [hasStaleData, setHasStaleData] = useState(false);
  const [searchInput, setSearchInput] = useState('');

  const reloadTournaments = async () => {
    const data = await apiFetch('/tournaments');

    // Extract array and metadata using utility function
    const { array: tournamentsArray, isStale } = extractArrayWithMetadata(data, 'tournaments');

    setTournaments(tournamentsArray);
    setHasStaleData(isStale);
  };

  // Debounced search input for filtering
  const [debouncedSearchInput, setDebouncedSearchInput] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearchInput(searchInput || '');
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput]);

  // Filtered tournaments based on search input
  const filteredTournaments = useMemo(() => {
    const tournamentsArray = Array.isArray(tournaments) ? tournaments : [];

    if (!debouncedSearchInput.trim()) {
      return tournamentsArray;
    }

    const searchTerms = debouncedSearchInput.toLowerCase().split(/\s+/).filter(Boolean);

    return tournamentsArray.filter(tournament => {
      const name = (tournament.name || '').toLowerCase();
      const location = (tournament.location || '').toLowerCase();

      return searchTerms.every(term =>
        name.includes(term) || location.includes(term)
      );
    });
  }, [tournaments, debouncedSearchInput]);

  useEffect(() => {
    reloadTournaments();
  }, []);

  return (
    <TournamentListContext.Provider value={{
      tournaments: filteredTournaments,
      allTournaments: tournaments,
      reloadTournaments,
      hasStaleData,
      searchInput,
      setSearchInput
    }}>
      {children}
    </TournamentListContext.Provider>
  );
}

export function useTournamentList() {
  return useContext(TournamentListContext);
}
