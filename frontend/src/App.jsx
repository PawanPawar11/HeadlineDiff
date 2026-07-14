import { useState } from 'react'
import { 
  History, 
  Search, 
  Sparkles, 
  ExternalLink, 
  AlertTriangle, 
  Check, 
  Clock, 
  Info, 
  ShieldAlert,
  Flame,
  Globe,
  Loader
} from 'lucide-react'
import './App.css'

const API_BASE = 'http://localhost:8000'

// Simple Word Diffing Algorithm
function wordDiff(oldStr, newStr) {
  if (!oldStr) return [{ type: 'added', text: newStr }];
  if (!newStr) return [{ type: 'removed', text: oldStr }];
  
  const oldWords = oldStr.split(/\s+/);
  const newWords = newStr.split(/\s+/);
  
  const dp = Array(oldWords.length + 1).fill(null).map(() => Array(newWords.length + 1).fill(0));
  
  for (let i = 1; i <= oldWords.length; i++) {
    for (let j = 1; j <= newWords.length; j++) {
      if (oldWords[i-1].toLowerCase() === newWords[j-1].toLowerCase()) {
        dp[i][j] = dp[i-1][j-1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
      }
    }
  }
  
  let i = oldWords.length;
  let j = newWords.length;
  const result = [];
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i-1].toLowerCase() === newWords[j-1].toLowerCase()) {
      result.unshift({ type: 'common', text: newWords[j-1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
      result.unshift({ type: 'added', text: newWords[j-1] });
      j--;
    } else {
      result.unshift({ type: 'removed', text: oldWords[i-1] });
      i--;
    }
  }
  return result;
}

function App() {
  const [activeTab, setActiveTab] = useState('url')
  
  // URL Tracker State (Mode A)
  const [urlInput, setUrlInput] = useState('')
  const [urlLoading, setUrlLoading] = useState(false)
  const [urlHistory, setUrlHistory] = useState(null)
  const [urlAnalysis, setUrlAnalysis] = useState(null)
  const [urlError, setUrlError] = useState(null)
  
  // Topic Analyzer State (Mode B)
  const [topicInput, setTopicInput] = useState('')
  const [selectedDomains, setSelectedDomains] = useState(['cnn.com', 'bbc.com'])
  const [topicLoading, setTopicLoading] = useState(false)
  const [topicResults, setTopicResults] = useState(null)
  const [topicAnalysis, setTopicAnalysis] = useState(null)
  const [topicError, setTopicError] = useState(null)

  const availableDomains = [
    { id: 'cnn.com', label: 'CNN', colorClass: 'cnn' },
    { id: 'foxnews.com', label: 'Fox News', colorClass: 'foxnews' },
    { id: 'nytimes.com', label: 'NYTimes', colorClass: 'nytimes' },
    { id: 'bbc.com', label: 'BBC', colorClass: 'bbc' }
  ]

  // Calculate dates relative to July 14, 2026
  const getMilestones = () => {
    const today = new Date('2026-07-14T00:00:00');
    const format = (d) => d.toISOString().slice(0, 10).replace(/-/g, '');
    
    const m1 = new Date(today); m1.setMonth(today.getMonth() - 1);
    const m3 = new Date(today); m3.setMonth(today.getMonth() - 3);
    const m6 = new Date(today); m6.setMonth(today.getMonth() - 6);
    const y1 = new Date(today); y1.setFullYear(today.getFullYear() - 1);
    
    return {
      "today": format(today),
      "1_month_ago": format(m1),
      "3_months_ago": format(m3),
      "6_months_ago": format(m6),
      "1_year_ago": format(y1)
    };
  };

  const handleDomainToggle = (domainId) => {
    if (selectedDomains.includes(domainId)) {
      setSelectedDomains(selectedDomains.filter(d => d !== domainId))
    } else {
      setSelectedDomains([...selectedDomains, domainId])
    }
  }

  // Submit URL Tracking (Mode A)
  const handleUrlSubmit = async (e, customUrl) => {
    if (e) e.preventDefault();
    const targetUrl = customUrl || urlInput;
    if (!targetUrl) return;

    setUrlLoading(true)
    setUrlError(null)
    setUrlHistory(null)
    setUrlAnalysis(null)

    try {
      const response = await fetch(`${API_BASE}/api/track-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl, sample_limit: 15 })
      })

      if (!response.ok) {
        throw new Error(`Server returned error status: ${response.status}`)
      }

      const data = await response.json()
      if (!data.history || data.history.length === 0) {
        setUrlError('No snapshot history found in the Wayback Machine for this URL. Please verify the URL.')
      } else {
        setUrlHistory(data.history)
        setUrlAnalysis(data.analysis)
      }
    } catch (err) {
      console.error(err)
      setUrlError('Connection to backend failed. Please ensure the backend API server is running on port 8000.')
    } finally {
      setUrlLoading(false)
    }
  }

  // Submit Topic Analysis (Mode B)
  const handleTopicSubmit = async (e, customTopic) => {
    if (e) e.preventDefault();
    const targetTopic = customTopic || topicInput;
    if (!targetTopic) return;
    if (selectedDomains.length === 0) {
      setTopicError('Please select at least one news outlet.')
      return;
    }

    setTopicLoading(true)
    setTopicError(null)
    setTopicResults(null)
    setTopicAnalysis(null)

    try {
      const response = await fetch(`${API_BASE}/api/search-topic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: targetTopic,
          domains: selectedDomains,
          milestones: getMilestones()
        })
      })

      if (!response.ok) {
        throw new Error(`Server returned error status: ${response.status}`)
      }

      const data = await response.json()
      // Check if any results were found
      const totalArticles = Object.values(data.results).reduce((sum, list) => sum + list.length, 0)
      if (totalArticles === 0) {
        setTopicError('No articles matching this topic were found on the archived section pages. Try a broader search keyword (e.g., "vaccine", "conflict", "election").')
      } else {
        setTopicResults(data.results)
        setTopicAnalysis(data.analysis)
      }
    } catch (err) {
      console.error(err)
      setTopicError('Connection to backend failed. Please ensure the backend API server is running on port 8000.')
    } finally {
      setTopicLoading(false)
    }
  }

  // Helper to load mock templates
  const loadUrlTemplate = (url) => {
    setUrlInput(url)
    handleUrlSubmit(null, url)
  }

  const loadTopicTemplate = (topic) => {
    setTopicInput(topic)
    handleTopicSubmit(null, topic)
  }

  // Render Diff Component
  const DiffRenderer = ({ oldText, newText }) => {
    const diff = wordDiff(oldText, newText);
    return (
      <div className="diff-container">
        {diff.map((item, idx) => (
          <span 
            key={idx} 
            className={`diff-word ${item.type}`}
          >
            {item.text}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1 className="brand-title">
          <Globe className="brand-logo-icon" size={48} />
          HeadlineDiff
        </h1>
        <p className="brand-subtitle">
          Deconstruct media bias and track how mainstream outlets rewrite their headlines and adapt their narratives over time.
        </p>
      </header>

      {/* Tabs */}
      <nav className="tab-container">
        <button 
          className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
          onClick={() => setActiveTab('url')}
        >
          <History size={18} />
          Stealth Edits Tracker
        </button>
        <button 
          className={`tab-btn ${activeTab === 'topic' ? 'active' : ''}`}
          onClick={() => setActiveTab('topic')}
        >
          <Search size={18} />
          Narrative Drift Analyzer
        </button>
      </nav>

      {/* Control Panel (Forms) */}
      {activeTab === 'url' ? (
        <form onSubmit={handleUrlSubmit} className="control-panel">
          <div className="input-group">
            <label className="input-label">
              <Globe size={18} />
              Analyze Headline Evolution (Single Article URL)
            </label>
            <input 
              type="url" 
              placeholder="Paste a news article URL (e.g. from BBC, CNN, NYTimes, Fox News)..." 
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              className="text-input"
              required
            />
          </div>
          <div className="action-row">
            <div className="templates-container">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Quick Test:</span>
              <button 
                type="button" 
                className="template-tag"
                onClick={() => loadUrlTemplate('https://www.bbc.com/news/uk-61585886')}
              >
                Queen Elizabeth II Death (BBC)
              </button>
            </div>
            <button type="submit" className="submit-btn" disabled={urlLoading}>
              {urlLoading ? <Loader className="animate-spin" size={18} style={{ animation: 'rotate 1s linear infinite' }} /> : <Sparkles size={18} />}
              Deconstruct Headline
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleTopicSubmit} className="control-panel">
          <div className="input-group">
            <label className="input-label">
              <Search size={18} />
              Topic Search Query
            </label>
            <input 
              type="text" 
              placeholder="Enter a keyword or phrase (e.g., 'vaccine', 'inflation', 'election')..." 
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              className="text-input"
              required
            />
          </div>

          <div className="input-group">
            <label className="input-label">
              <Globe size={18} />
              Target Outlets
            </label>
            <div className="domains-grid">
              {availableDomains.map(dom => (
                <div 
                  key={dom.id}
                  className={`domain-card ${selectedDomains.includes(dom.id) ? 'selected' : ''}`}
                  onClick={() => handleDomainToggle(dom.id)}
                >
                  <input 
                    type="checkbox" 
                    checked={selectedDomains.includes(dom.id)}
                    onChange={() => {}} // handled by card onClick
                    className="domain-checkbox"
                  />
                  <span className="domain-title">{dom.label}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{dom.id}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="action-row">
            <div className="templates-container">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Suggested Topics:</span>
              <button 
                type="button" 
                className="template-tag"
                onClick={() => loadTopicTemplate('inflation')}
              >
                Inflation
              </button>
              <button 
                type="button" 
                className="template-tag"
                onClick={() => loadTopicTemplate('vaccine')}
              >
                Vaccine
              </button>
            </div>
            <button type="submit" className="submit-btn" disabled={topicLoading}>
              {topicLoading ? <Loader className="animate-spin" size={18} style={{ animation: 'rotate 1s linear infinite' }} /> : <Sparkles size={18} />}
              Search Archives
            </button>
          </div>
        </form>
      )}

      {/* Loading Overlay */}
      {(urlLoading || topicLoading) && (
        <div className="spinner-container animate-fade-in">
          <div className="spinner"></div>
          <span className="loading-text">
            {urlLoading 
              ? 'Querying Internet Archive CDX and downloading snapshot frames...' 
              : 'Scanning historical news section indices at targeted milestones...'}
          </span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>This can take up to 30 seconds depending on Wayback Machine load.</span>
        </div>
      )}

      {/* Error Displays */}
      {urlError && <div className="control-panel animate-fade-in" style={{ borderColor: 'var(--danger)', background: 'var(--danger-bg)' }}>
        <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--danger)', fontWeight: 600 }}>
          <AlertTriangle size={20} />
          <span>Error</span>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>{urlError}</p>
      </div>}

      {topicError && <div className="control-panel animate-fade-in" style={{ borderColor: 'var(--danger)', background: 'var(--danger-bg)' }}>
        <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--danger)', fontWeight: 600 }}>
          <AlertTriangle size={20} />
          <span>Error</span>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>{topicError}</p>
      </div>}

      {/* URL Tracking Dashboard Results */}
      {activeTab === 'url' && urlHistory && (
        <div className="dashboard-grid animate-fade-in">
          {/* Timeline of edits */}
          <div className="timeline-card">
            <h2 className="timeline-title">
              <Clock className="ai-icon" size={24} />
              Headline Revision Timeline
            </h2>
            <div className="timeline-list">
              {urlHistory.map((item, idx) => (
                <div key={item.timestamp} className={`timeline-node ${item.changed ? 'changed' : ''}`}>
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <div className="timeline-time">
                        <Clock size={12} />
                        {new Date(item.datetime).toLocaleString()}
                      </div>
                      <span className={`timeline-badge ${item.changed ? 'edited' : 'original'}`}>
                        {item.changed ? `Revision ${idx}` : 'Original Publication'}
                      </span>
                    </div>
                    {item.changed ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Diff compared to previous version:</span>
                        <DiffRenderer oldText={urlHistory[idx - 1].headline} newText={item.headline} />
                      </div>
                    ) : (
                      <div className="headline-text">{item.headline}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Analysis */}
          <div className="analysis-panel">
            {urlAnalysis && (
              <div className="ai-card">
                <h2 className="ai-title">
                  <Sparkles className="ai-icon" size={24} />
                  AI Narrative Shift Report
                </h2>
                
                <div className="metrics-row">
                  <div className="metric-widget">
                    <div className={`metric-value ${
                      urlAnalysis.manipulation_index <= 3 ? 'rating-low' : 
                      urlAnalysis.manipulation_index <= 6 ? 'rating-mid' : 'rating-high'
                    }`}>
                      {urlAnalysis.manipulation_index}/10
                    </div>
                    <div className="metric-label">Framing Index</div>
                  </div>
                  <div className="metric-widget">
                    <div className="metric-value" style={{ fontSize: '1rem', fontWeight: 600 }}>
                      {urlAnalysis.sentiment_shift || 'Neutral'}
                    </div>
                    <div className="metric-label">Sentiment Shift</div>
                  </div>
                </div>

                <div className="ai-section">
                  <div className="ai-section-title">Executive Summary</div>
                  <p className="ai-text">{urlAnalysis.summary}</p>
                </div>

                <div className="ai-section">
                  <div className="ai-section-title">Narrative Shift & Goal</div>
                  <p className="ai-text">{urlAnalysis.narrative_shift}</p>
                </div>

                <div className="ai-section">
                  <div className="ai-section-title">Linguistic Framing Techniques</div>
                  <div className="framing-pills">
                    {urlAnalysis.framing_techniques && urlAnalysis.framing_techniques.length > 0 ? (
                      urlAnalysis.framing_techniques.map((tech, i) => (
                        <span key={i} className="framing-pill">{tech}</span>
                      ))
                    ) : (
                      <span className="ai-text" style={{ fontSize: '0.85rem' }}>No significant manipulation detected in edits.</span>
                    )}
                  </div>
                </div>

                <div className="ai-section" style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
                  <div className="ai-section-title" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Info size={12} />
                    Original vs Final Headline
                  </div>
                  <p className="ai-text" style={{ margin: '0.5rem 0 0.25rem 0', fontStyle: 'italic', fontSize: '0.85rem' }}>
                    <strong>Original:</strong> "{urlHistory[0].headline}"
                  </p>
                  <p className="ai-text" style={{ margin: '0', fontStyle: 'italic', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    <strong>Latest:</strong> "{urlHistory[urlHistory.length - 1].headline}"
                  </p>
                </div>
              </div>
            )}
            
            {/* Disclaimer */}
            <div className="control-panel" style={{ padding: '1.25rem', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem' }}>
                <ShieldAlert size={18} />
                <span>Media Tracking Note</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0, lineHeight: 1.4 }}>
                Stealth editing refers to changing the content or tone of a published headline without explicitly adding a correction notice. While minor corrections are normal, shifting verbs, blame, or emotional priming terms often indicates narrative drift.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Topic Drift Analyzer Results */}
      {activeTab === 'topic' && topicResults && (
        <div className="dashboard-grid wide animate-fade-in">
          {/* AI report on drift (stands out at the top) */}
          {topicAnalysis && (
            <div className="ai-card" style={{ marginBottom: '1rem' }}>
              <h2 className="ai-title">
                <Sparkles className="ai-icon" size={24} />
                AI Topic Narrative Evolution Report
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
                <div className="metrics-row" style={{ gridTemplateColumns: '1fr' }}>
                  <div className="metric-widget" style={{ flexDirection: 'row', gap: '1.5rem', justifyContent: 'flex-start', padding: '1.5rem' }}>
                    <div className="metric-widget" style={{ background: 'transparent', border: 'none', padding: 0 }}>
                      <div className={`metric-value ${
                        topicAnalysis.polarization_rating <= 3 ? 'rating-low' : 
                        topicAnalysis.polarization_rating <= 6 ? 'rating-mid' : 'rating-high'
                      }`}>
                        {topicAnalysis.polarization_rating}/10
                      </div>
                      <div className="metric-label">Polarization Index</div>
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div className="ai-section-title">Polarization Context</div>
                      <p className="ai-text" style={{ margin: 0 }}>{topicAnalysis.polarization_explanation || 'Average polarization across periods.'}</p>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr md:1fr', gap: '1.5rem' }}>
                  <div className="ai-section">
                    <div className="ai-section-title">Evolution Executive Summary</div>
                    <p className="ai-text">{topicAnalysis.executive_summary}</p>
                  </div>
                  
                  <div className="ai-section">
                    <div className="ai-section-title">Bias & Stance Evolution</div>
                    <p className="ai-text">{topicAnalysis.bias_evolution}</p>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr md:1fr', gap: '1.5rem' }}>
                  <div className="ai-section">
                    <div className="ai-section-title">Likely Editorial Intent</div>
                    <p className="ai-text">{topicAnalysis.editorial_intent}</p>
                  </div>
                  
                  <div className="ai-section">
                    <div className="ai-section-title">Key Buzzwords & Framing Tokens</div>
                    <div className="framing-pills" style={{ marginTop: '0.25rem' }}>
                      {topicAnalysis.key_buzzwords && topicAnalysis.key_buzzwords.length > 0 ? (
                        topicAnalysis.key_buzzwords.map((word, i) => (
                          <span key={i} className="framing-pill" style={{ background: 'rgba(6, 182, 212, 0.1)', color: '#22d3ee', borderColor: 'rgba(6, 182, 212, 0.2)' }}>{word}</span>
                        ))
                      ) : (
                        <span className="ai-text" style={{ fontSize: '0.85rem' }}>No repetitive buzzwords detected.</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Historical timeline layout */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <h2 className="timeline-title" style={{ margin: 0 }}>
              <History className="ai-icon" size={24} />
              Milestone Headlines Output
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
              {/* Periods order: 1 year ago, 6 months, 3 months, 1 month, today */}
              {['1_year_ago', '6_months_ago', '3_months_ago', '1_month_ago', 'today'].map(period => {
                const list = topicResults[period] || [];
                const milestoneDesc = topicAnalysis?.timeline_milestones?.[period] || 
                                      topicAnalysis?.timeline_milestones?.[period.replace('_', ' ')] || 
                                      'Historical captures.';
                
                return (
                  <div key={period} className="topic-period-card">
                    <div className="period-header">
                      <div className="period-title">
                        <Clock size={16} />
                        {period.replace(/_/g, ' ')}
                      </div>
                      <span className="period-subtitle">{list.length} articles</span>
                    </div>

                    {/* Brief AI summary of this specific period */}
                    {topicAnalysis && (
                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', gap: '0.25rem' }}>
                        <Info size={14} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--accent-primary)' }} />
                        <span>{milestoneDesc}</span>
                      </div>
                    )}

                    <div className="article-list">
                      {list.length > 0 ? (
                        list.map((art, idx) => {
                          const domainMatch = availableDomains.find(d => art.url.includes(d.id));
                          const domainClass = domainMatch ? domainMatch.colorClass : 'generic';
                          const domainLabel = domainMatch ? domainMatch.label : new URL(art.url).hostname;
                          
                          return (
                            <div key={idx} className="topic-article-item">
                              <span className={`source-badge ${domainClass}`}>{domainLabel}</span>
                              <div className="article-headline">"{art.headline}"</div>
                              <a href={art.url} target="_blank" rel="noopener noreferrer" className="article-footer-link">
                                Source Capture
                                <ExternalLink size={12} />
                              </a>
                            </div>
                          );
                        })
                      ) : (
                        <div className="empty-state" style={{ padding: '2rem' }}>
                          <AlertTriangle className="empty-icon" size={24} />
                          <span style={{ fontSize: '0.85rem' }}>No headlines matching query terms.</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Empty State when no searches performed yet */}
      {!urlHistory && !topicResults && !urlLoading && !topicLoading && (
        <div className="empty-state animate-fade-in" style={{ background: 'var(--bg-surface)', padding: '4rem 2rem' }}>
          <History className="empty-icon" size={64} style={{ opacity: 0.15, marginBottom: '0.5rem' }} />
          <h2 style={{ margin: 0, color: 'var(--text-primary)' }}>No Analysis Performed Yet</h2>
          <p style={{ maxWidth: '400px', margin: '0 auto', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            {activeTab === 'url' 
              ? 'Paste an article link above or click the Queen Elizabeth template to watch the WayBack Machine crawler extract stealth updates.' 
              : 'Enter a topic keyword (like "vaccine" or "inflation") to pull headlines and track editorial changes over the past year.'}
          </p>
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>HeadlineDiff • Designed for Media Transparency & Integrity</p>
        <p style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
          Historical data sourced in real-time from the Internet Archive Wayback Machine. Linguistic reports powered by Google Gemini AI.
        </p>
      </footer>
    </div>
  )
}

export default App
