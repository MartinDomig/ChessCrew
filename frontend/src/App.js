import React, { useEffect, useState } from 'react';
import { apiFetch } from './api';
import CreateAdmin from './CreateAdmin';
import LoginForm from './LoginForm';
import MainWindow from './MainWindow';
import NetworkStatus from './NetworkStatus';
import { Box, CircularProgress, CssBaseline } from '@mui/material';
import './pwa.css';

function App() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
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
          const isLoggedIn = data && data.logged_in;
          setLoggedIn(isLoggedIn);
          setUser(data);
        })
        .catch(() => {
          setLoggedIn(false);
          setUser(null);
        })
        .finally(() => setCheckingLogin(false));
    }
  }, [state]);

  // Listen for authentication errors
  useEffect(() => {
    const handleAuthError = () => {
      console.log('Authentication error detected, logging out');
      setLoggedIn(false);
      setUser(null);
    };

    window.addEventListener('auth-error', handleAuthError);
    return () => window.removeEventListener('auth-error', handleAuthError);
  }, []);

  const handleAdminCreated = () => {
    setState({ ...state, needs_admin: false });
  };

  const handleLogin = () => {
    setLoggedIn(true);
    // Refetch user after login
    apiFetch('/session/user').then(setUser);
  };

  return (
    <>
      <CssBaseline />
      <NetworkStatus />
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {(loading || checkingLogin) ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress />
        </Box>
      ) : state && state.needs_admin ? (
        <CreateAdmin onCreated={handleAdminCreated} />
      ) : !loggedIn ? (
        <LoginForm onLogin={handleLogin} />
      ) : (
        <MainWindow user={user} />
      )}
    </>
  );
}

export default App;
