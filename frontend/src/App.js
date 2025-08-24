import React, { useEffect, useState } from 'react';
import { apiFetch } from './api';
import CreateAdmin from './CreateAdmin';
import { CssBaseline, Container } from '@mui/material';

function App() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/state')
      .then(data => {
        setState(data);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleAdminCreated = () => {
    setState({ ...state, needs_admin: false });
  };

  return (
    <>
      <CssBaseline />
      <Container maxWidth="sm">
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        {loading ? (
          <p>Loading...</p>
        ) : state && state.needs_admin ? (
          <CreateAdmin onCreated={handleAdminCreated} />
        ) : (
          <div>
            <h1>ChessCrew React Frontend</h1>
            <p>Welcome! This is your new React frontend. Connect to your backend at <code>/api</code>.</p>
          </div>
        )}
      </Container>
    </>
  );
}

export default App;
