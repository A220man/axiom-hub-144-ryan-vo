import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth({ status: 'error', service: 'axiom-hub' }));

    fetch('/api/version')
      .then(res => res.json())
      .then(data => setVersion(data))
      .catch(() => setVersion({ version: 'unknown', name: 'axiom-hub-144-ryan-vo' }));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Axiom Hub</h1>
        <p className="tagline">The design language that makes your AI harness better at design</p>
        <div className="status-card">
          <h2>Backend Status</h2>
          {health && (
            <div className={`status ${health.status}`}>
              <span>Status: {health.status}</span>
              <span>Service: {health.service}</span>
            </div>
          )}
          {version && (
            <div className="version-info">
              <span>Version: {version.version}</span>
              <span>Name: {version.name}</span>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

export default App;
