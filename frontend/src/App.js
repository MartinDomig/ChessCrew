import React, { useEffect, useState } from 'react';
import { apiFetch } from './api';
import CreateAdmin from './CreateAdmin';
import LoginForm from './LoginForm';
import MainWindow from './MainWindow';
import { CssBaseline, Container } from '@mui/material';

function App() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [checkingLogin, setCheckingLogin] = useState(false);

  useEffect(() => {
    apiFetch('/state')
      .then(data => {
        setState(data);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (state && !state.needs_admin) {
      setCheckingLogin(true);
      apiFetch('/session/user')
        .then(data => {
          setLoggedIn(data && data.logged_in);
        })
        .catch(() => setLoggedIn(false))
        .finally(() => setCheckingLogin(false));
    }
  }, [state]);

  const handleAdminCreated = () => {
    setState({ ...state, needs_admin: false });
  };

  const handleLogin = () => {
    setLoggedIn(true);
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
        ) : checkingLogin ? (
          <p>Checking login...</p>
        ) : !loggedIn ? (
          <LoginForm onLogin={handleLogin} />
        ) : (
          <MainWindow />
        )}
      </Container>
    </>
  );
}

export default App;
