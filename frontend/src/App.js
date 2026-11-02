import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);
  const [context, setContext] = useState(null);
  const [contextValidation, setContextValidation] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth({ status: 'error', service: 'axiom-hub' }));

    fetch('/api/version')
      .then(res => res.json())
      .then(data => setVersion(data))
      .catch(() => setVersion({ version: 'unknown', name: 'axiom-hub-144-ryan-vo' }));

    fetch('/api/context/resolve')
      .then(res => res.json())
      .then(data => setContext(data))
      .catch(() => setContext({ product: null, design: null, config_path: null }));

    fetch('/api/context/validate')
      .then(res => res.json())
      .then(data => setContextValidation(data))
      .catch(() => setContextValidation({ valid: false, errors: ['Failed to fetch'], warnings: [], paths: {} }));
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
        <div className="status-card">
          <h2>Context Resolution</h2>
          {context && (
            <div className="context-info">
              <div className={`context-item ${context.product ? 'found' : 'missing'}`}>
                <span className="context-label">PRODUCT.md:</span>
                <span className="context-value">
                  {context.product ? context.product : 'Not found'}
                </span>
              </div>
              <div className={`context-item ${context.design ? 'found' : 'missing'}`}>
                <span className="context-label">DESIGN.md:</span>
                <span className="context-value">
                  {context.design ? context.design : 'Not found'}
                </span>
              </div>
              {context.config_path && (
                <div className="context-item">
                  <span className="context-label">Config:</span>
                  <span className="context-value">{context.config_path}</span>
                </div>
              )}
            </div>
          )}
          {contextValidation && (
            <div className="validation-info">
              <div className={`validation-status ${contextValidation.valid ? 'valid' : 'invalid'}`}>
                {contextValidation.valid ? '✓ Valid' : '✗ Invalid'}
              </div>
              {contextValidation.warnings.length > 0 && (
                <div className="validation-warnings">
                  {contextValidation.warnings.map((w, i) => (
                    <span key={i} className="warning">{w}</span>
                  ))}
                </div>
              )}
              {contextValidation.errors.length > 0 && (
                <div className="validation-errors">
                  {contextValidation.errors.map((e, i) => (
                    <span key={i} className="error">{e}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </header>
    </div>
  );
}
export default App;

