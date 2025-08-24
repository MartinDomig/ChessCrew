import React, { useEffect, useState } from 'react';
import { apiFetch } from './api';

function App() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);


  useEffect(() => {
    apiFetch('/state')
      .then(setState)
      .catch(err => setError(err.message));
  }, []);

  return (
    <div style={{ padding: '2em' }}>
      <h1>ChessCrew React Frontend</h1>
      <p>process.env: {JSON.stringify(process.env, null, 2)}</p>
      <p>Welcome! This is your new React frontend. Connect to your backend at <code>/api</code>.</p>
      <h2>Backend State</h2>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {state ? (
        <pre>{JSON.stringify(state, null, 2)}</pre>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default App;
