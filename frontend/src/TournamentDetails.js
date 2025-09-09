import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import SaveIcon from '@mui/icons-material/Save';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import React, { useEffect, useState } from 'react';

import { apiFetch } from './api';
import TournamentResults from './TournamentResults';
import TournamentTypeIndicator from './TournamentTypeIndicator';

// Custom hook for tournament data management
function useTournamentData(tournamentId) {
  const [players, setPlayers] = useState([]);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tournamentId) return;

    const fetchTournamentData = async () => {
      setLoading(true);
      setError('');
      try {
        const [playersData, gamesData] = await Promise.all([
          apiFetch(`/tournaments/${tournamentId}/players`),
          apiFetch(`/tournaments/${tournamentId}/games`)
        ]);
        
        // Ensure data is in correct format (handle potential cache issues)
        const playersArray = Array.isArray(playersData) ? playersData : 
                           (playersData && typeof playersData === 'object' && Object.keys(playersData).every(key => /^\d+$/.test(key))) ?
                           Object.values(playersData) : [];
        const gamesArray = Array.isArray(gamesData) ? gamesData : 
                          (gamesData && typeof gamesData === 'object' && Object.keys(gamesData).every(key => /^\d+$/.test(key))) ?
                          Object.values(gamesData) : [];
        
        setPlayers(playersArray);
        setGames(gamesArray);
      } catch (err) {
        setError('Fehler beim Laden der Turnierdaten');
        console.error('Error fetching tournament data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTournamentData();
  }, [tournamentId]);

  return { players, games, loading, error };
}

// Custom hook for edit mode management
function useEditMode(tournament) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTournament, setEditedTournament] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (tournament) {
      setEditedTournament({
        name: tournament.name || '',
        date: formatDateForInput(tournament.date),
        location: tournament.location || '',
        is_team: tournament.is_team || false
      });
    }
  }, [tournament]);

  const toggleEdit = () => {
    setIsEditing(!isEditing);
    if (!isEditing && tournament) {
      resetEditedTournament();
    }
  };

  const resetEditedTournament = () => {
    setEditedTournament({
      name: tournament.name || '',
      date: formatDateForInput(tournament.date),
      location: tournament.location || '',
      is_team: tournament.is_team || false
    });
  };

  const updateField = (field, value) => {
    setEditedTournament(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCancel = () => {
    setIsEditing(false);
    resetEditedTournament();
  };

  return {
    isEditing,
    editedTournament,
    saving,
    setSaving,
    toggleEdit,
    updateField,
    handleCancel
  };
}

// Utility functions
const formatDisplayDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return !isNaN(date) ? date.toLocaleDateString() : dateString.split('T')[0];
};

const formatDateForInput = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  if (!isNaN(date)) {
    return date.toISOString().split('T')[0];
  }
  // If it's already in YYYY-MM-DD format, return as is
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return dateString;
  }
  // Fallback: try to extract date part
  return dateString.split('T')[0] || '';
};

// Sub-components
function TournamentHeader({ tournament, isEditing, editedTournament, onFieldChange, onToggleEdit, onCancel }) {
  return (
    <CardHeader
      title={
        isEditing ? (
          <TextField
          fullWidth
          label="Turniername"
          value={editedTournament.name}
          onChange={(e) => onFieldChange('name', e.target.value)}
          variant="outlined"
          size="small"
          />
        ) : (
          tournament.name
        )
      }
      action={
        isEditing ? (
          <IconButton onClick={onCancel} color="secondary">
            <CloseIcon />
          </IconButton>
        ) : (
          <IconButton onClick={onToggleEdit} color="primary">
            <EditIcon />
          </IconButton>
        )
      }
      />
  );
}

function TournamentDetailsForm({ tournament, isEditing, editedTournament, onFieldChange, participantCount, onSave, onDelete, saving }) {
  return (
    <CardContent sx={{ pt: 1 }}>
      {isEditing ? (
        <>
          <TextField
            fullWidth
            label="Datum"
            type="date"
            value={editedTournament.date}
            onChange={(e) => onFieldChange('date', e.target.value)}
            variant="outlined"
            size="small"
            sx={{ mb: 2 }}
            slotProps={{
              inputLabel: {
                shrink: true
              }
            }}
          />
          <TextField
            fullWidth
            label="Ort"
            value={editedTournament.location}
            onChange={(e) => onFieldChange('location', e.target.value)}
            variant="outlined"
            size="small"
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={editedTournament.is_team}
                onChange={(e) => onFieldChange('is_team', e.target.checked)}
                color="primary"
              />
            }
            label="Mannschaftsturnier"
            sx={{ mb: 2 }}
          />
          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'space-between' }}>
            <Button
              variant="contained"
              color="error"
              onClick={onDelete}
              sx={{ minWidth: 120, flex: 1 }}
            >
              <DeleteIcon />
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={onSave}
              disabled={saving}
              sx={{ minWidth: 120, flex: 1 }}
            >
              {saving ? <CircularProgress size={20} /> : <SaveIcon />}
            </Button>
          </Box>
        </>
      ) : (
        <>
          <Typography variant="subtitle1">Datum: {formatDisplayDate(tournament.date)}</Typography>
          <Typography variant="body2">Ort: {tournament.location}</Typography>
          <Typography variant="body2">Teilnehmer: {participantCount}</Typography>
          <Typography variant="body2">Runden: {tournament.rounds}</Typography>
          <Typography variant="body2">Typ: {tournament.is_team ? 'Mannschaftsturnier' : 'Einzelturnier'}</Typography>
          {tournament.elo_rating && <Typography variant="body2">Wertung: {tournament.elo_rating}</Typography>}
          {tournament.time_control && <Typography variant="body2">Bedenkzeit: {tournament.time_control}</Typography>}
        </>
      )}
    </CardContent>
  );
}

function LoadingState() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
      <CircularProgress />
    </Box>
  );
}

function ErrorState({ error }) {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography color="error">{error}</Typography>
      </CardContent>
    </Card>
  );
}

// Main component
function TournamentDetails({ tournament, onPlayerClick, onDelete, onUpdate }) {
  const [localTournament, setLocalTournament] = useState(tournament);
  const { players, games, loading, error } = useTournamentData(localTournament?.id);
  const {
    isEditing,
    editedTournament,
    saving,
    setSaving,
    toggleEdit,
    updateField,
    handleCancel
  } = useEditMode(localTournament);

  const [selectedPlayer, setSelectedPlayer] = useState(null);

  // Update local tournament state when prop changes
  useEffect(() => {
    setLocalTournament(tournament);
  }, [tournament]);

  if (!localTournament) return null;

  const handlePlayerClick = async (player) => {
    if (!player.player_id) return;

    try {
      const data = await apiFetch(`/players/${player.player_id}`);
      if (onPlayerClick) {
        onPlayerClick(data, localTournament);
      } else {
        setSelectedPlayer(data);
      }
    } catch (err) {
      console.error('Error fetching player details:', err);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updatedTournament = await apiFetch(`/tournaments/${localTournament.id}`, {
        method: 'PUT',
        body: editedTournament
      });

      // Update local state immediately
      setLocalTournament(updatedTournament);
      
      // Notify parent component
      if (onUpdate) {
        onUpdate(updatedTournament);
      }
      toggleEdit();
    } catch (err) {
      console.error('Error saving tournament:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Sind Sie sicher, dass Sie dieses Turnier löschen möchten?')) return;

    try {
      await apiFetch(`/tournaments/${localTournament.id}`, { method: 'DELETE' });
      if (onDelete) {
        onDelete(localTournament.id);
      }
    } catch (err) {
      alert(err.message || 'Fehler beim Löschen des Turniers');
      console.error('Error deleting tournament:', err);
    }
  };

  return (
    <Box sx={{ p: 1, maxWidth: '100%' }}>
      <Card sx={{ mb: 2 }}>
        <TournamentTypeIndicator tournament={localTournament} size="small" />
        <TournamentHeader
          tournament={localTournament}
          isEditing={isEditing}
          editedTournament={editedTournament}
          onFieldChange={updateField}
          onToggleEdit={toggleEdit}
          onCancel={handleCancel}
        />
        <TournamentDetailsForm
          tournament={localTournament}
          isEditing={isEditing}
          editedTournament={editedTournament}
          onFieldChange={updateField}
          participantCount={players.length}
          onSave={handleSave}
          onDelete={handleDelete}
          saving={saving}
        />
      </Card>

      {loading && <LoadingState />}
      {error && <ErrorState error={error} />}

      {!loading && players.length > 0 && (
        <TournamentResults players={players} onPlayerClick={handlePlayerClick} />
      )}
    </Box>
  );
}

export default TournamentDetails;
