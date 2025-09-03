import React, { useState } from 'react';
import { Box, Typography, CircularProgress, TextField, Button, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { apiFetch } from './api';

export default function PlayerNotes({ playerId }) {
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
      
      // Ensure notesData is always an array
      let notesArray = [];
      if (Array.isArray(notesData)) {
        notesArray = notesData;
      } else if (notesData && typeof notesData === 'object') {
        // Handle case where cache returns array-like object
        const keys = Object.keys(notesData).filter(key => key !== '_isStale' && key !== '_cacheAge');
        const isArrayLike = keys.length > 0 && keys.every(key => /^\d+$/.test(key));
        
        if (isArrayLike) {
          // Convert array-like object to proper array
          const maxIndex = Math.max(...keys.map(k => parseInt(k, 10)));
          notesArray = Array.from({ length: maxIndex + 1 }, (_, i) => notesData[i]).filter(item => item !== undefined);
        } else {
          // Check for nested data structure
          if (Array.isArray(notesData.notes)) {
            notesArray = notesData.notes;
          } else if (Array.isArray(notesData.data)) {
            notesArray = notesData.data;
          }
        }
      }
      
      console.log('Processed notes data:', { isArray: Array.isArray(notesArray), length: notesArray.length });
      setNotes(notesArray);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchNotes();
  }, [playerId]);

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
