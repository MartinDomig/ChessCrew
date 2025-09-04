import React, { useEffect, useState } from 'react';
import { IconButton, Card, CardContent, Typography, Box, CircularProgress } from '@mui/material';
import TagManager from './TagManager';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DeleteIcon from '@mui/icons-material/Delete';
import CategoryChip from './CategoryChip';
import TagChip from './TagChip';
import PlayerActiveStar from './PlayerActiveStar';
import TournamentStatsChip from './TournamentStatsChip';
import { apiFetch, invalidatePlayerCaches } from './api';
import { reconstructArray } from './arrayUtils';
import PlayerNotes from './PlayerNotes';
import { countryCodeToFlag } from './countryUtils';
import ContactInfo from './ContactInfo';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';

export default function PlayerDetailsCard({ player, onPlayerUpdated, onTournamentClick }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [localPlayer, setLocalPlayer] = useState(player);
  const [tagModalOpen, setTagModalOpen] = useState(false);
  const [playerTagsKey, setPlayerTagsKey] = useState(0);
  const [tournaments, setTournaments] = useState([]);
  const [tournamentsLoading, setTournamentsLoading] = useState(false);
  const [tournamentsError, setTournamentsError] = useState(null);
  const [contactEditing, setContactEditing] = useState(false);
  const [tournamentEditing, setTournamentEditing] = useState(false);

  useEffect(() => {
    setNotes(player.notes || []);
    setLoading(false);
    setLocalPlayer(player);
    
    // Check if tournaments are already embedded in player data (offline mode)
    if (player.tournaments && Array.isArray(player.tournaments)) {
      console.log('Using embedded tournaments data:', player.tournaments.length);
      setTournaments(player.tournaments);
      setTournamentsLoading(false);
      setTournamentsError(null);
    } else {
      // Fetch tournament history from API if not embedded
      fetchTournaments();
    }
  }, [player.id]);

  useEffect(() => {
    setLocalPlayer(player);
  }, [player]);

  const fetchTournaments = async () => {
    // First check if we already have embedded tournaments data
    if (player.tournaments && Array.isArray(player.tournaments)) {
      console.log('Using embedded tournaments data (from fetchTournaments):', player.tournaments.length);
      setTournaments(player.tournaments);
      setTournamentsLoading(false);
      setTournamentsError(null);
      return;
    }

    setTournamentsLoading(true);
    setTournamentsError(null);
    try {
      const data = await apiFetch(`/players/${player.id}/tournaments`);
      
      // Use utility function to reconstruct array
      const tournamentsArray = reconstructArray(data, 'tournaments');
      
      console.log('Fetched tournaments data:', { isArray: Array.isArray(tournamentsArray), length: tournamentsArray.length });
      setTournaments(tournamentsArray);
    } catch (err) {
      console.error('Failed to fetch tournaments:', err);
      
      // Check if we're offline and provide a friendlier message
      if (!navigator.onLine) {
        setTournamentsError('Offline - Turniere nicht verfügbar. Bitte mit Internet verbinden und erneut versuchen.');
      } else if (err.message && err.message.includes('offline')) {
        setTournamentsError('Verbindung zum Server nicht möglich. Turniere werden möglicherweise nicht aktuell angezeigt.');
      } else {
        setTournamentsError(`Turniere konnten nicht geladen werden: ${err.message}`);
      }
    } finally {
      setTournamentsLoading(false);
    }
  };

  // Fetch all tags when modal opens
  const handleOpenTagModal = () => {
    setTagModalOpen(true);
  };

  const onTagDelete = async (tag) => {
    console.log('delte tag', tag);
    try {
      if (window.confirm(`Tag "${tag.name}" wirklich entfernen?`)) {
        await apiFetch(`/players/${player.id}/tags/${tag.id}`, { method: 'DELETE' });
        
        // Invalidate both players list cache AND individual player cache
        await invalidatePlayerCaches(player.id);
        
        const updated = await apiFetch(`/players/${player.id}`);
        setLocalPlayer(updated);
        setPlayerTagsKey(prev => prev + 1);
        
        if (onPlayerUpdated) onPlayerUpdated(updated);
      }
    } catch (err) {
      console.error(err);
      
      // If deletion failed (e.g., tag already removed), refresh player data to sync UI
      if (err.message && err.message.includes('nicht zugewiesen')) {
        console.log('Tag was not assigned, refreshing player data to sync UI');
        try {
          // Invalidate cache first to force fresh data
          await invalidatePlayerCaches(player.id);
          
          const updated = await apiFetch(`/players/${player.id}`);
          setLocalPlayer(updated);
          setPlayerTagsKey(prev => prev + 1);
          
          if (onPlayerUpdated) onPlayerUpdated(updated);
        } catch (refreshErr) {
          console.error('Failed to refresh player data:', refreshErr);
        }
      }
    }
  };

  const handleTournamentDisassociate = async (tournamentPlayerId, tournamentName) => {
    if (!window.confirm(`Möchten Sie "${player.first_name} ${player.last_name}" wirklich vom Turnier "${tournamentName}" entfernen?`)) {
      return;
    }

    try {
      await apiFetch(`/tournament-players/${tournamentPlayerId}/disassociate`, {
        method: 'PUT'
      });
      
      // Refresh the tournaments list - this will check for embedded data first
      await fetchTournaments();
      
      // Refresh player data to update any related state
      if (onPlayerUpdated) {
        try {
          const updatedPlayer = await apiFetch(`/players/${player.id}`);
          onPlayerUpdated(updatedPlayer);
        } catch (refreshErr) {
          console.error('Failed to refresh player data after tournament disassociation:', refreshErr);
          // Don't show error to user, the disassociation was successful
        }
      }
    } catch (error) {
      console.error('Failed to disassociate from tournament:', error);
      if (!navigator.onLine) {
        alert('Offline - Änderungen können nicht gespeichert werden. Bitte mit Internet verbinden und erneut versuchen.');
      } else {
        alert(`Fehler beim Entfernen vom Turnier: ${error.message}`);
      }
    }
  };

  const handleContactEditToggle = () => {
    if (contactEditing) {
      setLocalPlayer(player);
      setContactEditing(false);
    } else {
      setContactEditing(true);
    }
  };

  const handleTournamentEditToggle = () => {
    setTournamentEditing(!tournamentEditing);
  };

  return (
    <Card sx={{ mb: 2, position: 'relative' }}>
      <PlayerActiveStar player={player} />
      <CardContent>
        <Typography color="text.secondary">
          <small>{player.p_number ? `ID: ${player.p_number}` : ''} {player.fide_number ? ` FIDE: ${player.fide_number}` : ''}</small>
        </Typography>
        <Typography variant="h5">
          {player.first_name}, {player.last_name} {countryCodeToFlag(player.citizen)} {player.female ? '♛' : '♚'} <CategoryChip player={player} />
          <TournamentStatsChip player={player} />
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          {player.club}
        </Typography>
        {(player.elo > 0 || player.fide_elo > 0) && (
          <Typography sx={{ mb: 1 }}>
              <strong>ELO:</strong> {player.elo ?? ''} / {player.fide_elo ?? ''}
          </Typography>
        )}
        <Typography sx={{ mb: 1 }}>
            <strong>Geburtsdatum:</strong> {player.birthday ? new Date(player.birthday).toLocaleDateString('de-DE') : ''}
        </Typography>
        {/* Contact Info Header with Edit/Cancel Button */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ color: 'text.secondary', fontWeight: 'medium' }}>
            Kontakt
          </Typography>
          <IconButton
            onClick={handleContactEditToggle}
            sx={{
              color: 'primary.main',
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(4px)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 1)',
                transform: 'scale(1.05)'
              },
              transition: 'all 0.2s ease-in-out',
              size: 'small'
            }}
            aria-label={contactEditing ? "Bearbeitung abbrechen" : "Kontaktinformationen bearbeiten"}
            title={contactEditing ? "Bearbeitung abbrechen" : "Kontaktinformationen bearbeiten"}
          >
            {contactEditing ? <CloseIcon fontSize="small" /> : <EditIcon fontSize="small" />}
          </IconButton>
        </Box>
        <ContactInfo player={localPlayer} onPlayerUpdated={onPlayerUpdated} contactEditing={contactEditing} onEditClick={handleContactEditToggle} onEditClose={() => setContactEditing(false)} />
        <Box sx={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', pt: 1, gap: 1, width: '100%' }}>
          <IconButton
            color="primary"
            size="large"
            onClick={handleOpenTagModal}
            aria-label="Tag hinzufügen"
            sx={{ p: 0, alignSelf: 'center', verticalAlign: 'middle' }}
          >
            <AddCircleOutlineIcon fontSize="large" />
          </IconButton>
          {localPlayer.tags && localPlayer.tags.map(tag => (
            <TagChip
              key={`player-${localPlayer.id}-tag-${tag.id}`}
              tag={tag}
              onDelete={onTagDelete}
            />
          ))}
        </Box>
        <TagManager
          player={player}
          open={tagModalOpen}
          onClose={async () => {
            setTagModalOpen(false);
            const updated = await apiFetch(`/players/${player.id}`);
            setLocalPlayer(updated);
            setPlayerTagsKey(k => k + 1);
            if (onPlayerUpdated) onPlayerUpdated(updated);
          }}
          onTagAdded={
            async () => {
              setTagModalOpen(false);
              
              // Invalidate both players list cache AND individual player cache
              await invalidatePlayerCaches(player.id);
              
              const updated = await apiFetch(`/players/${player.id}`);
              setLocalPlayer(updated);
              setPlayerTagsKey(k => k + 1);
              
              if (onPlayerUpdated) onPlayerUpdated(updated);
            }
          }
        />
        <Box sx={{ mt: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ color: 'primary.main' }}>
              Turniere
            </Typography>
            <IconButton
              onClick={handleTournamentEditToggle}
              sx={{
                color: 'primary.main',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(4px)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 1)',
                  transform: 'scale(1.05)'
                },
                transition: 'all 0.2s ease-in-out',
                size: 'small'
              }}
              aria-label={tournamentEditing ? "Bearbeitung abbrechen" : "Turniere bearbeiten"}
              title={tournamentEditing ? "Bearbeitung abbrechen" : "Turniere bearbeiten"}
            >
              {tournamentEditing ? <CloseIcon fontSize="small" /> : <EditIcon fontSize="small" />}
            </IconButton>
          </Box>
          
          {tournamentsLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          )}
          
          {tournamentsError && (
            <Typography color="error" sx={{ mb: 2 }}>
              {tournamentsError}
            </Typography>
          )}
          
          {!tournamentsLoading && tournaments.length === 0 && (
            <Typography color="text.secondary">
              Keine Turniere gefunden.
            </Typography>
          )}
          
          {!tournamentsLoading && tournaments.length > 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {tournaments.map((tournament, index) => {
                const dateStr = tournament.date 
                  ? new Date(tournament.date).toLocaleDateString('de-DE')
                  : '';
                
                const locationAndDate = [tournament.location, dateStr].filter(Boolean).join(' • ');
                
                const resultText = [
                  tournament.rank && tournament.total_players ? `Rang ${tournament.rank}/${tournament.total_players}` : 
                  tournament.rank ? `Rang ${tournament.rank}` : null,
                  tournament.points !== null && tournament.games_played !== undefined ? `${tournament.points}/${tournament.games_played}` : null
                ].filter(Boolean).join(' • ');
                
                return (
                  <Card 
                    key={tournament.id || index} 
                    sx={{ 
                      backgroundColor: '#fafafa',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: '#f0f0f0',
                        transform: 'translateY(-1px)',
                        boxShadow: 2
                      },
                      transition: 'all 0.2s ease-in-out'
                    }}
                    onClick={() => onTournamentClick && onTournamentClick({ id: tournament.tournament_id, name: tournament.tournament_name })}
                  >
                    <CardContent sx={{ py: 2, position: 'relative' }}>
                      {tournamentEditing && (
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent card click
                            handleTournamentDisassociate(tournament.id, tournament.tournament_name);
                          }}
                          sx={{
                            position: 'absolute',
                            top: 8,
                            right: 8,
                            color: 'error.main',
                            '&:hover': {
                              backgroundColor: 'error.light',
                              color: 'white'
                            }
                          }}
                          title={`"${player.first_name} ${player.last_name}" vom Turnier entfernen`}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      )}
                      <Typography variant="subtitle2" sx={{ fontWeight: 'medium', pr: tournamentEditing ? 4 : 0 }}>
                        {tournament.tournament_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" >
                        {locationAndDate || '-'}
                      </Typography>
                      <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
                        {resultText || 'Keine Ergebnisse'}
                      </Typography>
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          )}
        </Box>
        
        <Box sx={{ mt: 4 }}>
          <PlayerNotes playerId={player.id} initialNotes={player.notes} />
        </Box>
      </CardContent>
    </Card>
  );
}
