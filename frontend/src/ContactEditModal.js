import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, Typography } from '@mui/material';

export default function ContactEditModal({
  open,
  onClose,
  onSave,
  loading,
  error,
  initialEmail = '',
  initialPhone = '',
  initialAddress = '',
  initialZip = '',
  initialTown = '',
}) {
  const [email, setEmail] = useState(initialEmail);
  const [phone, setPhone] = useState(initialPhone);
  const [address, setAddress] = useState(initialAddress);
  const [zip, setZip] = useState(initialZip);
  const [town, setTown] = useState(initialTown);

  useEffect(() => {
    if (open) {
      setEmail(initialEmail);
      setPhone(initialPhone);
      setAddress(initialAddress);
      setZip(initialZip);
      setTown(initialTown);
    }
  }, [open, initialEmail, initialPhone, initialAddress, initialZip, initialTown]);

  const handleSave = () => {
    onSave({ email, phone, address, zip, town });
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Bearbeite Kontaktinformationen</DialogTitle>
      <DialogContent>
        <TextField
          label="E-Mail"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          fullWidth
          margin="normal"
          inputMode="email"
        />
        <TextField
          label="Telefon"
          type="text"
          value={phone}
          onChange={e => setPhone(e.target.value)}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Adresse"
          type="text"
          value={address}
          onChange={e => setAddress(e.target.value)}
          fullWidth
          margin="normal"
        />
        <TextField
          label="PLZ"
          type="text"
          value={zip}
          onChange={e => setZip(e.target.value)}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Ort"
          type="text"
          value={town}
          onChange={e => setTown(e.target.value)}
          fullWidth
          margin="normal"
        />
        {error && (
          <Typography color="error" sx={{ mt: 1 }}>{error}</Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          Abbrechen
        </Button>
        <Button onClick={handleSave} disabled={loading} variant="contained" color="primary">
          {loading ? 'Speichern...' : 'Speichern'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
