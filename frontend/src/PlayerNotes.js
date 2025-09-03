import React, { useState } from 'react';
import { Box, Typography, CircularProgress, TextField, Button, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { apiFetch } from './api';
import { reconstructArray } from './arrayUtils';

export default function PlayerNotes({ playerId, initialNotes = null }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [noteInput, setNoteInput] = useState('');
  const [addingNote, setAddingNote] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState(null);

  const fetchNotes = async () => {
    setLoading(true);
    setNotes([]);
    setError(null);
    try {
      const notesData = await apiFetch(`/players/${playerId}/notes`);
      
      // Use utility function to reconstruct array
      const notesArray = reconstructArray(notesData, 'notes');
      
      console.log('Processed notes data:', { isArray: Array.isArray(notesArray), length: notesArray.length });
      setNotes(notesArray);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    // If initialNotes are provided (offline mode), use them instead of fetching
    if (initialNotes && Array.isArray(initialNotes)) {
      console.log('Using embedded notes data:', initialNotes.length);
      setNotes(initialNotes);
      setLoading(false);
      setError(null);
    } else {
      // Fetch notes from API if not embedded
      fetchNotes();
    }
  }, [playerId, initialNotes]);

  const handleSaveNote = async () => {
    setAddingNote(true);
    try {
      if (editingNoteId) {
        await apiFetch(`/players/${playerId}/notes/${editingNoteId}`, {
          method: 'PATCH',
          body: { content: noteInput }
        });
      } else {
        await apiFetch(`/players/${playerId}/notes`, {
          method: 'POST',
          body: { content: noteInput }
        });
      }
      setNoteInput('');
      setEditingNoteId(null);
      fetchNotes();
    } catch (err) {
      setError(err.message);
    } finally {
      setAddingNote(false);
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Notiz wirklich löschen?')) return;
    setLoading(true);
    try {
      await apiFetch(`/players/${playerId}/notes/${noteId}`, { method: 'DELETE' });
      fetchNotes();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>Notizen</Typography>
      {loading ? (
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
          <CircularProgress size={24} sx={{ mr: 2 }} />
          <Typography>Lade Notizen...</Typography>
        </Box>
      ) : error ? (
        <Typography color="error">Fehler beim Laden der Notizen: {error}</Typography>
      ) : !Array.isArray(notes) || notes.length === 0 ? (
        <Typography color="text.secondary">Keine Notizen vorhanden.</Typography>
      ) : (
        (Array.isArray(notes) ? notes : []).map(note => (
          <Box key={note.id} sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {note.manual === true && note.updated_at ? `Geändert: ${new Date(note.updated_at).toLocaleString('de-DE')}` : note.created_at}
              </Typography>
              <Typography>{note.content}</Typography>
            </Box>
            {note.manual === true && (
              <>
                <IconButton
                  size="small"
                  color="primary"
                  sx={{ ml: 2 }}
                  onClick={() => {
                    setEditingNoteId(note.id);
                    setNoteInput(note.content);
                  }}
                  aria-label="Notiz bearbeiten"
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  sx={{ ml: 1 }}
                  onClick={() => handleDeleteNote(note.id)}
                  aria-label="Notiz löschen"
                >
                  <DeleteIcon />
                </IconButton>
              </>
            )}
          </Box>
        ))
      )}
      <Box sx={{ mt: 2 }}>
        <TextField
          label={editingNoteId ? "Notiz bearbeiten" : "Neue Notiz"}
          multiline
          fullWidth
          value={noteInput || ''}
          onChange={e => setNoteInput(e.target.value)}
          sx={{ mb: 1 }}
        />
        <Button
          variant="contained"
          color="primary"
          disabled={!noteInput || addingNote}
          onClick={handleSaveNote}
        >
          {editingNoteId ? "Notiz bearbeiten" : "Notiz hinzufügen"}
        </Button>
        {editingNoteId && (
          <Button
            variant="text"
            color="inherit"
            sx={{ ml: 1 }}
            onClick={() => {
              setEditingNoteId(null);
              setNoteInput('');
            }}
          >
            Abbrechen
          </Button>
        )}
      </Box>
    </Box>
  );
}
