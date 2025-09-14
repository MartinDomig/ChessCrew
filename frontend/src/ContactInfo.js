import React, { useState, useEffect } from 'react';
import { IconButton, Typography, Button, Box, CircularProgress, TextField } from '@mui/material';
import PhoneIcon from '@mui/icons-material/Phone';
import EmailIcon from '@mui/icons-material/Email';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { apiFetch } from './api';

export default function ContactInfo({ player, onPlayerUpdated, contactEditing, onEditClick, onEditClose }) {
  const [localPlayer, setLocalPlayer] = useState(player);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLocalPlayer(player);
  }, [player]);

  const handleContactSave = async () => {
    setSaving(true);
    try {
      const updatedPlayer = await apiFetch(`/players/${player.id}`, {
        method: 'PUT',
        body: {
          email: localPlayer.email,
          email_alternate: localPlayer.email_alternate,
          phone: localPlayer.phone,
          address: localPlayer.address,
          zip: localPlayer.zip,
          town: localPlayer.town,
        },
      });

      setLocalPlayer(updatedPlayer);
      onPlayerUpdated(updatedPlayer);
      if (onEditClose) onEditClose();
    } catch (error) {
      console.error('Error updating player contact info:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ position: 'relative' }}>
      {/* Address Section */}
      {(contactEditing || [localPlayer.address, localPlayer.zip, localPlayer.town].some(Boolean)) && (
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }}>
          {contactEditing ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, flex: 1 }}>
              <TextField
                fullWidth
                size="small"
                label="Adresse"
                value={localPlayer.address || ''}
                onChange={(e) => setLocalPlayer(prev => ({ ...prev, address: e.target.value }))}
                variant="outlined"
              />
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="PLZ"
                  value={localPlayer.zip || ''}
                  onChange={(e) => setLocalPlayer(prev => ({ ...prev, zip: e.target.value }))}
                  variant="outlined"
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Ort"
                  value={localPlayer.town || ''}
                  onChange={(e) => setLocalPlayer(prev => ({ ...prev, town: e.target.value }))}
                  variant="outlined"
                />
              </Box>
            </Box>
          ) : (
            <>
              <LocationOnIcon sx={{ mr: 1, color: 'text.secondary', flexShrink: 0 }} />
              <Typography sx={{ flex: 1 }}>
                {[localPlayer.address, localPlayer.zip, localPlayer.town].filter(Boolean).join(', ')}
              </Typography>
            </>
          )}
        </Box>
      )}

      {/* Email Section */}
      {(contactEditing || localPlayer.email) && (
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }}>
          {contactEditing ? (
            <TextField
              fullWidth
              size="small"
              label="E-Mail"
              value={localPlayer.email || ''}
              onChange={(e) => setLocalPlayer(prev => ({ ...prev, email: e.target.value }))}
              variant="outlined"
              sx={{ flex: 1 }}
            />
          ) : (
            <>
              <EmailIcon sx={{ mr: 1, color: 'text.secondary', flexShrink: 0 }} />
              <Typography sx={{ flex: 1 }}>
                {localPlayer.email
                  ? localPlayer.email
                  .split(/[,;\s]+/)
                  .filter(e => e)
                  .map((email, idx) => (
                    <React.Fragment key={email}>
                          <a href={`mailto:${email}`}>{email}</a>
                          {idx < localPlayer.email.split(/[,;\s]+/).filter(e => e).length - 1 ? ', ' : ''}
                        </React.Fragment>
                      ))
                      : null}
              </Typography>
            </>
          )}
        </Box>
      )}

      {/* Alternate Email Section */}
      {(contactEditing || localPlayer.email_alternate) && (
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }}>
          {contactEditing ? (
            <TextField
              fullWidth
              size="small"
              label="Alternative E-Mail"
              value={localPlayer.email_alternate || ''}
              onChange={(e) => setLocalPlayer(prev => ({ ...prev, email_alternate: e.target.value }))}
              variant="outlined"
              sx={{ flex: 1 }}
            />
          ) : (
            <>
              <EmailIcon sx={{ mr: 1, color: 'text.secondary', flexShrink: 0 }} />
              <Typography sx={{ flex: 1 }}>
                {localPlayer.email_alternate
                  ? localPlayer.email_alternate
                  .split(/[,;\s]+/)
                  .filter(e => e)
                  .map((email, idx) => (
                    <React.Fragment key={email}>
                          <a href={`mailto:${email}`}>{email}</a>
                          {idx < localPlayer.email_alternate.split(/[,;\s]+/).filter(e => e).length - 1 ? ', ' : ''}
                        </React.Fragment>
                      ))
                      : null}
              </Typography>
            </>
          )}
        </Box>
      )}

      {/* Phone Section */}
      {(contactEditing || localPlayer.phone) && (
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }}>
          {contactEditing ? (
            <TextField
              fullWidth
              size="small"
              label="Telefon"
              value={localPlayer.phone || ''}
              onChange={(e) => setLocalPlayer(prev => ({ ...prev, phone: e.target.value }))}
              variant="outlined"
              sx={{ flex: 1 }}
            />
          ) : (
            <>
              <PhoneIcon sx={{ mr: 1, color: 'text.secondary', flexShrink: 0 }} />
              <Typography sx={{ flex: 1 }}>
                {localPlayer.phone ? localPlayer.phone : null}
              </Typography>
            </>
          )}
        </Box>
      )}

      {/* Save Button */}
      {contactEditing && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleContactSave}
            disabled={saving}
            sx={{ minWidth: 120 }}
          >
            {saving ? <CircularProgress size={20} /> : 'Speichern'}
          </Button>
        </Box>
      )}
    </Box>
  );
}
