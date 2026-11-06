import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);
  const [context, setContext] = useState(null);
  const [contextValidation, setContextValidation] = useState(null);
  const [gitignoreInit, setGitignoreInit] = useState(null);
  const [gitignoreStatus, setGitignoreStatus] = useState(null);
  const [gitignoreResult, setGitignoreResult] = useState(null);
  const [loading, setLoading] = useState(false);

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

    fetch('/api/gitignore/init')
      .then(res => res.json())
      .then(data => setGitignoreInit(data))
      .catch(() => setGitignoreInit({ missing_count: 0, categories: {} }));

    fetch('/api/gitignore/status')
      .then(res => res.json())
      .then(data => setGitignoreStatus(data))
      .catch(() => setGitignoreStatus({ gitignore_exists: false, missing_entries: 0 }));
  }, []);

  const handleGitignoreAdd = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/gitignore/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_add: true }),
      });
      const data = await res.json();
      setGitignoreResult(data);
      // Refresh status
      const statusRes = await fetch('/api/gitignore/status');
      const statusData = await statusRes.json();
      setGitignoreStatus(statusData);
    } catch (e) {
      setGitignoreResult({ error: 'Failed to add entries' });
    } finally {
      setLoading(false);
    }
  };

  const handleGitignoreClean = async (dryRun = true) => {
    setLoading(true);
    try {
      const res = await fetch('/api/gitignore/clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: dryRun, include_worktrees: true }),
      });
      const data = await res.json();
      setGitignoreResult(data);
    } catch (e) {
      setGitignoreResult({ error: 'Failed to clean' });
    } finally {
      setLoading(false);
    }
  };

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
        <div className="status-card">
          <h2>Gitignore Management</h2>
          {gitignoreInit && (
            <div className="gitignore-info">
              <div className="gitignore-stats">
                <span>Missing entries: {gitignoreInit.missing_count}</span>
                <span>Total defaults: {gitignoreInit.total_default_count}</span>
              </div>
              <div className="gitignore-categories">
                {Object.entries(gitignoreInit.categories || {}).map(([cat, entries]) => (
                  <div key={cat} className="gitignore-category">
                    <h4>{cat.replace('_', ' ')}</h4>
                    <ul>
                      {(entries || []).slice(0, 3).map((e, i) => (
                        <li key={i}><code>{e.pattern}</code> - {e.description}</li>
                      ))}
                      {(entries || []).length > 3 && (
                        <li>... and {(entries || []).length - 3} more</li>
                      )}
                    </ul>
                  </div>
                ))}
              </div>
              <button 
                onClick={handleGitignoreAdd} 
                disabled={loading || gitignoreInit.missing_count === 0}
                className="action-button"
              >
                {loading ? 'Adding...' : 'Add Missing Entries'}
              </button>
            </div>
          )}
          {gitignoreStatus && (
            <div className="gitignore-status">
              <div className={`status-item ${gitignoreStatus.gitignore_exists ? 'exists' : 'missing'}`}>
                .gitignore: {gitignoreStatus.gitignore_exists ? 'Exists' : 'Not found'}
              </div>
              <div className="status-item">
                Existing entries: {gitignoreStatus.existing_entries}
              </div>
              <div className="status-item">
                Missing entries: {gitignoreStatus.missing_entries}
              </div>
              {gitignoreStatus.worktree_roots && gitignoreStatus.worktree_roots.length > 0 && (
                <div className="status-item">
                  Worktrees: {gitignoreStatus.worktree_roots.length}
                </div>
              )}
            </div>
          )}
          {gitignoreResult && (
            <div className="gitignore-result">
              {gitignoreResult.error && (
                <div className="error-message">Error: {gitignoreResult.error}</div>
              )}
              {gitignoreResult.added && (
                <div className="success-message">
                  Added {gitignoreResult.count} entries to .gitignore
                </div>
              )}
              {gitignoreResult.removed_files !== undefined && (
                <div className={`result-message ${gitignoreResult.dry_run ? 'dry-run' : ''}`}>
                  {gitignoreResult.dry_run ? 'Dry run - ' : ''}
                  Would remove {gitignoreResult.removed_files.length} files and {gitignoreResult.removed_dirs.length} directories
                  {gitignoreResult.bytes_freed > 0 && (
                    <span> ({formatBytes(gitignoreResult.bytes_freed)})</span>
                  )}
                </div>
              )}
              <div className="clean-buttons">
                <button 
                  onClick={() => handleGitignoreClean(true)} 
                  disabled={loading}
                  className="action-button secondary"
                >
                  Dry Run Clean
                </button>
                <button 
                  onClick={() => handleGitignoreClean(false)} 
                  disabled={loading}
                  className="action-button danger"
                >
                  Clean Generated Files
                </button>
              </div>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
export default App;

