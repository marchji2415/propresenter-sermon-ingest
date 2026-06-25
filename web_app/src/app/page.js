"use client";

import React, { useState, useRef } from 'react';

export default function Home() {
  // Input settings states
  const [file, setFile] = useState(null);
  const [location, setLocation] = useState('midtown');
  const [translation, setTranslation] = useState('');
  const [useAi, setUseAi] = useState(false);
  const [apiKey, setApiKey] = useState('');

  // Processing states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('slides');
  const [checkedMedia, setCheckedMedia] = useState({});

  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  // Handle Drag & Drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      const ext = droppedFile.name.split('.').pop().toLowerCase();
      if (ext === 'pdf' || ext === 'docx') {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Only PDF and DOCX notes files are supported.');
      }
    }
  };

  // Handle File Input Change
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  // Remove Selected File
  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Trigger File Input Click
  const handleDropzoneClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please upload a notes file first.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('location', location);
    formData.append('translation', translation);
    formData.append('useAi', useAi.toString());
    formData.append('apiKey', apiKey);

    try {
      const response = await fetch('/api/ingest', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.details || 'An unexpected error occurred during ingestion.');
      }

      setResult(data);
      setCheckedMedia({}); // Reset checklist state
      setActiveTab('slides'); // Default to slides preview
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Toggle checklist items
  const toggleMediaCheck = (idx) => {
    setCheckedMedia(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  // Format Python stdout logs with color indicators
  const renderLogLines = (stdout) => {
    if (!stdout) return null;
    const lines = stdout.split('\n');
    return lines.map((line, idx) => {
      let className = 'log-entry';
      if (line.includes('[OK]')) className += ' success';
      else if (line.includes('[INFO]')) className += ' info';
      else if (line.includes('[WARN]')) className += ' warning';
      else if (line.includes('[ERROR]') || line.includes('Error')) className += ' error';
      return (
        <div key={idx} className={className}>
          {line}
        </div>
      );
    });
  };

  return (
    <div>
      {/* Header section — control room status bar */}
      <header className="hero-band">
        <div className="hero-content">
          <div className="logo-group">
            <h1>
              <span>●</span> Sermon Ingest
            </h1>
            <p>ProPresenter compiler · Sunday screens production line</p>
          </div>
          <div className="header-actions">
            {result && (
              <a
                href={`/api/download?id=${result.taskId}&filename=${file.name.replace(/\.[^/.]+$/, "")}_slides.pro`}
                className="btn-download"
                id="download-pro-btn"
              >
                <span>↓</span> Download .pro
              </a>
            )}
          </div>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="app-container">
        <div className="dashboard-grid">

        {/* Left Column: Configuration Settings */}
        <aside className="glass-panel glowing">
          <h2 className="config-title">
            <span>▸</span> Input Config
          </h2>

          <form onSubmit={handleSubmit}>
            {/* Upload Zone */}
            <div className="form-group">
              <label>Sermon Notes File</label>
              <div
                className={`dropzone-container ${dragOver ? 'active' : ''}`}
                id="dropzone-area"
                onClick={handleDropzoneClick}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.docx"
                  style={{ display: 'none' }}
                  id="notes-file-input"
                />

                {file ? (
                  <div>
                    <span className="dropzone-icon" style={{ fontSize: '2rem' }}>📄</span>
                    <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Notes loaded</p>
                    <div className="file-selected-badge">
                      <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                      <button type="button" onClick={handleRemoveFile} title="Remove file">&times;</button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <span className="dropzone-icon">📥</span>
                    <p className="dropzone-text">
                      Drag & drop your sermon notes here, or <span className="dropzone-highlight">browse</span>
                    </p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      Supports PDF or Word Document (.docx)
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Location Theme Select */}
            <div className="form-group">
              <label htmlFor="location-select">Location / Screen Theme</label>
              <select
                id="location-select"
                className="select-control"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              >
                <option value="midtown">Midtown (Landscape 1920x1080)</option>
                <option value="downtown">Downtown (Vertical 840x1080)</option>
              </select>
            </div>

            {/* Translation Selection */}
            <div className="form-group">
              <label htmlFor="translation-select">Bible Translation Override</label>
              <select
                id="translation-select"
                className="select-control"
                value={translation}
                onChange={(e) => setTranslation(e.target.value)}
              >
                <option value="">Default (detect from notes / ESV)</option>
                <option value="NASB">NASB (New American Standard Bible)</option>
                <option value="ESV">ESV (English Standard Version)</option>
                <option value="BSB">BSB (Berean Standard Bible)</option>
                <option value="WEB">WEB (World English Bible)</option>
                <option value="KJV">KJV (King James Version)</option>
              </select>
            </div>

            {/* AI Toggle Switch */}
            <div className="form-group">
              <div className="toggle-group">
                <span style={{ fontSize: '0.85rem', fontWeight: '500' }}>AI Ingestion Agent</span>
                <label className="switch">
                  <input
                    type="checkbox"
                    id="ai-toggle"
                    checked={useAi}
                    onChange={(e) => setUseAi(e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem', lineHeight: '1.3' }}>
                Uses Gemini agentic scripture parsing and slide splitting. If disabled, high-accuracy structural heuristics are used.
              </p>
            </div>

            {/* API Key Override (Optional) */}
            <div className="form-group">
              <label htmlFor="api-key-input">Gemini API Key (Optional)</label>
              <input
                type="password"
                id="api-key-input"
                className="input-control"
                placeholder="••••••••••••••••••••••••"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                Overrides server env config. Left empty to use system default.
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn-primary"
              id="submit-ingest-btn"
              disabled={loading || !file}
            >
              {loading ? 'Compiling…' : 'Compile Presentation'}
            </button>
          </form>
        </aside>

        {/* Right Column: Execution Output / Slide Deck Inspection */}
        <main className="main-dashboard">

          {/* Case 1: Initial Empty Screen */}
          {!loading && !error && !result && (
            <div className="glass-panel dashboard-empty">
              <div className="dashboard-empty-icon">📡</div>
              <h3>Standing by for sermon notes</h3>
              <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', textAlign: 'center', maxWidth: '400px', color: 'var(--text-secondary)' }}>
                Load a PDF or DOCX in the input panel and run the compiler to populate the program monitor with slides.
              </p>
            </div>
          )}

          {/* Case 2: Loading State */}
          {loading && (
            <div className="glass-panel loading-container">
              <div className="loading-spinner"></div>
              <h3>Compiling slides & fetching scripture</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem', textAlign: 'center' }}>
                Parsing notes, resolving Bible references, running verse-split heuristics, and assembling the ProPresenter protobuf payload.
              </p>
            </div>
          )}

          {/* Case 3: Error State */}
          {error && (
            <div className="glass-panel" style={{ borderColor: 'rgba(255, 68, 56, 0.35)' }}>
              <h3 style={{ color: 'var(--status-live)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span>⚠</span> Ingestion failed
              </h3>
              <p style={{ background: 'rgba(255, 68, 56, 0.06)', border: '1px solid rgba(255, 68, 56, 0.25)', padding: '1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', color: '#ff9a91', whiteSpace: 'pre-wrap', marginBottom: '1rem', fontFamily: 'var(--font-mono)' }}>
                {error}
              </p>
              <h4 style={{ fontSize: '0.78rem', marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Troubleshooting</h4>
              <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: '1.6' }}>
                <li>Make sure your Gemini API Key is valid if using the AI Ingestion Agent.</li>
                <li>Verify your notes file is formatted correctly.</li>
                <li>If an API quota issue is encountered, disable the "AI Ingestion Agent" to fall back to the robust manual parser.</li>
              </ul>
            </div>
          )}

          {/* Case 4: Success - Results Screen */}
          {result && (
            <>
              {/* Compilation Status Banner */}
              <div className="status-banner">
                <div className="status-info">
                  <span className="status-badge">Compiled</span>
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: '600' }}>Presentation ready for playback</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {result.report.slides.length} slides · {result.report.media_notes.length} media cues
                    </p>
                  </div>
                </div>
                <a
                  href={`/api/download?id=${result.taskId}&filename=${file.name.replace(/\.[^/.]+$/, "")}_slides.pro`}
                  className="btn-download"
                >
                  <span>↓</span> Download .pro
                </a>
              </div>

              {/* Tabs for Navigation */}
              <div className="tabs-navigation">
                <button
                  className={`tab-btn ${activeTab === 'slides' ? 'active' : ''}`}
                  onClick={() => setActiveTab('slides')}
                  id="tab-slides"
                >
                  Slides ({result.report.slides.length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'media' ? 'active' : ''}`}
                  onClick={() => setActiveTab('media')}
                  id="tab-media"
                >
                  Shot List ({result.report.media_notes.length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
                  onClick={() => setActiveTab('logs')}
                  id="tab-logs"
                >
                  Logs
                </button>
              </div>

              {/* Tab Content 1: Slides Deck Preview Grid (Program Monitor) */}
              {activeTab === 'slides' && (
                <div className={`theme-${result.report.location}`}>
                  <div className="slides-grid">
                    {result.report.slides.map((slide, idx) => (
                      <div key={idx} className={`slide-card ${slide.kind.toLowerCase()}-slide`}>
                        <div className="slide-header">
                          <span className="slide-number">
                            SL {String(idx + 1).padStart(2, '0')} / {String(result.report.slides.length).padStart(2, '0')}
                          </span>
                          <span className={`slide-badge ${slide.kind.toLowerCase()}`}>
                            {slide.kind.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="slide-body-container">
                          <div className="slide-text-preview">
                            {slide.body}
                          </div>
                        </div>
                        <div className="slide-footer" title={slide.name}>
                          {slide.name}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab Content 2: Creative & Media Checklist */}
              {activeTab === 'media' && (
                <div className="media-section">
                  <h3 style={{ fontSize: '1.05rem', fontWeight: '600' }}>Graphics & media cue list</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Detected inside brackets/parentheses or explicitly noted for the production team. Check items off as they're added to ProPresenter.
                  </p>

                  {result.report.media_notes.length === 0 ? (
                    <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-secondary)' }}>
                      No media instruction cues, graphics requests, or side notes were detected in this sermon document.
                    </div>
                  ) : (
                    result.report.media_notes.map((note, idx) => {
                      const lines = note.text.split('\n');
                      const title = lines[0];
                      const description = lines.slice(1).join('\n');
                      const isChecked = !!checkedMedia[idx];

                      return (
                        <div
                          key={idx}
                          className="media-card"
                          style={{ opacity: isChecked ? 0.55 : 1 }}
                        >
                          <input
                            type="checkbox"
                            className="media-checkbox"
                            id={`media-chk-${idx}`}
                            checked={isChecked}
                            onChange={() => toggleMediaCheck(idx)}
                          />
                          <div className="media-content">
                            <div className="media-title" style={{ textDecoration: isChecked ? 'line-through' : 'none' }}>
                              {title}
                            </div>
                            {description && (
                              <div className="media-desc" style={{ textDecoration: isChecked ? 'line-through' : 'none' }}>
                                {description}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* Tab Content 3: Compiler Execution Terminal Logs */}
              {activeTab === 'logs' && (
                <div>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: '600', marginBottom: '1rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
                    Python engine console output
                  </h3>
                  <div className="log-panel">
                    {renderLogLines(result.stdout)}
                  </div>
                </div>
              )}
            </>
          )}

        </main>

        </div>
      </div>
    </div>
  );
}