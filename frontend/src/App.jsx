import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot, faSpinner, faUpload, faFileVideo, faCopy, faTrashAlt, faEnvelope, faCheckCircle, faChartBar, faEye, faCogs, faMagic, faLink, faVideo, faFile, faHistory, faClock } from '@fortawesome/free-solid-svg-icons';
import { faTwitter, faLinkedin, faGithub } from '@fortawesome/free-brands-svg-icons';

const BACKEND_URL = 'http://127.0.0.1:8000';

const loadingMessages = [
  "Initializing neural network pathways...",
  "Analyzing video frames with quantum algorithms...",
  "Synthesizing deep learning models...",
  "Optimizing AI perception matrices...",
  "Calibrating computational vision cores...",
  "Deploying autonomous reasoning subroutines...",
  "Mapping high-dimensional data manifolds...",
  "Stabilizing heuristic inference engines...",
  "Activating multi-modal cognition layers...",
];

function App() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [inputType, setInputType] = useState('file'); // 'file' or 'url'
  const [analysisType, setAnalysisType] = useState('auto');
  const [customPrompt, setCustomPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [refinements, setRefinements] = useState([]); // Array of refinement objects
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [analysisTypes, setAnalysisTypes] = useState({});
  const [copySuccess, setCopySuccess] = useState('');
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [isFirstUpload, setIsFirstUpload] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  
  // Refinement states - moved to per-refinement tracking
  const [refiningIndex, setRefiningIndex] = useState(null); // null means not refining, -1 = original, 0+ is refinement index
  const [refinementPrompts, setRefinementPrompts] = useState({}); // Track prompts per index
  
  // Ref for auto-scrolling to result
  const resultRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchAnalysisTypes();
    loadStateFromStorage();
    loadHistoryFromStorage();
  }, []);

  // Load state from localStorage
  const loadStateFromStorage = () => {
    try {
      const savedState = localStorage.getItem('frameInsight_currentAnalysis');
      if (savedState) {
        const parsed = JSON.parse(savedState);
        if (parsed.result) setResult(parsed.result);
        if (parsed.refinements) setRefinements(parsed.refinements);
        if (parsed.analysisType) setAnalysisType(parsed.analysisType);
      }
    } catch (error) {
      console.error('Error loading state:', error);
    }
  };

  // Load history from localStorage
  const loadHistoryFromStorage = () => {
    try {
      const savedHistory = localStorage.getItem('frameInsight_history');
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory));
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  // Save current analysis to localStorage
  useEffect(() => {
    if (result) {
      try {
        localStorage.setItem('frameInsight_currentAnalysis', JSON.stringify({
          result,
          refinements,
          analysisType,
          timestamp: new Date().toISOString()
        }));
      } catch (error) {
        console.error('Error saving state:', error);
      }
    }
  }, [result, refinements, analysisType]);

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prevProgress + 1;
        });
        setLoadingMessageIndex((prevIndex) => (prevIndex + 1) % loadingMessages.length);
      }, 3000); // Slowed from 1000ms to 3000ms
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (result && resultRef.current) {
        // Smooth scroll to result after short delay to allow rendering
        setTimeout(() => {
            resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
  }, [result]);

  const fetchAnalysisTypes = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/analysis_types`);
      setAnalysisTypes(response.data);
    } catch (error) {
      console.error('Error fetching analysis types:', error);
    }
  };

  const saveToHistory = (analysisData) => {
    try {
      const newHistory = [
        {
          id: Date.now(),
          ...analysisData
        },
        ...history
      ].slice(0, 50); // Keep last 50 analyses
      
      setHistory(newHistory);
      localStorage.setItem('frameInsight_history', JSON.stringify(newHistory));
    } catch (error) {
      console.error('Error saving to history:', error);
    }
  };

  const loadFromHistory = (historyItem) => {
    setResult(historyItem.result);
    setRefinements(historyItem.refinements || []);
    setAnalysisType(historyItem.analysisType);
    setCustomPrompt(historyItem.customPrompt || '');
    setShowHistory(false);
    // Scroll to result
    setTimeout(() => {
      resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const deleteHistoryItem = (id) => {
    const newHistory = history.filter(item => item.id !== id);
    setHistory(newHistory);
    localStorage.setItem('frameInsight_history', JSON.stringify(newHistory));
  };

  const clearAllHistory = () => {
    if (confirm('Are you sure you want to clear all history? This cannot be undone.')) {
      setHistory([]);
      localStorage.removeItem('frameInsight_history');
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set to false if leaving the dropzone itself
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const droppedFile = files[0];
      if (droppedFile.type.startsWith('video/')) {
        setFile(droppedFile);
        setInputType('file');
        setError(null);
      } else {
        setError('Please drop a video file (MP4, MOV, AVI, WebM)');
      }
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (inputType === 'file' && !file) {
      setError('Please select a video file.');
      return;
    }
    if (inputType === 'url' && !url) {
      setError('Please enter a video URL.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setRefinements([]); // Reset refinements
    setRefinementPrompts({}); // Clear refinement prompts
    setProgress(0);
    setLoadingMessageIndex(0);

    const formData = new FormData();
    if (inputType === 'file' && file) {
      formData.append('file', file);
    } else if (inputType === 'url' && url) {
      formData.append('url', url);
    }
    formData.append('analysis_type', analysisType);
    if (analysisType === 'custom') {
      formData.append('custom_prompt', customPrompt);
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          // Only update progress up to 50% for upload, rest is processing
          setProgress(Math.min(percentCompleted, 50));
        },
      });
      
      console.log("Response received:", response.data);
      
      // Check if the response contains an error
      if (response.data?.error) {
        setError(response.data.error);
      } else {
        setResult(response.data);
        setIsFirstUpload(false);
        console.log("Result set successfully:", response.data);
        
        // Save to history
        saveToHistory({
          result: response.data,
          analysisType,
          customPrompt,
          filename: file?.name || url || 'Unknown',
          timestamp: new Date().toISOString()
        });
      }
      setProgress(100);
    } catch (error) {
      console.error("Axios error:", error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || 'An error occurred during processing.';
      setError(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRefine = async (sourceIndex = -1) => {
      const promptKey = `prompt_${sourceIndex}`;
      const promptValue = refinementPrompts[promptKey];
      
      if (!promptValue || !promptValue.trim()) return;
      
      // Determine source analysis
      const sourceAnalysis = sourceIndex === -1 ? result.analysis : refinements[sourceIndex].analysis;
      const sourceType = sourceIndex === -1 ? result.analysis_type : refinements[sourceIndex].analysis_type;
      
      setRefiningIndex(sourceIndex);
      try {
          const response = await axios.post(`${BACKEND_URL}/refine`, {
              original_analysis: typeof sourceAnalysis === 'string' ? sourceAnalysis : JSON.stringify(sourceAnalysis),
              refinement_prompt: promptValue,
              analysis_type: sourceType || analysisType
          });
          
          // Add new refinement to the array
          const newRefinement = {
              analysis: response.data.analysis,
              analysis_type: sourceType || analysisType,
              refined_from: sourceIndex,
              prompt_used: promptValue,
              timestamp: new Date().toISOString()
          };
          
          setRefinements([...refinements, newRefinement]);
          
          // Clear the specific prompt
          setRefinementPrompts(prev => {
              const updated = {...prev};
              delete updated[promptKey];
              return updated;
          });
          
      } catch (error) {
          console.error("Refinement error:", error);
          alert("Failed to refine analysis. Please try again.");
      } finally {
          setRefiningIndex(null);
      }
  };

  const clearCache = async () => {
    try {
      await axios.post(`${BACKEND_URL}/clear_cache`);
      // Reset all state
      setResult(null);
      setRefinements([]);
      setRefinementPrompts({});
      setFile(null);
      setUrl('');
      setError(null);
      setProgress(0);
      setLoadingMessageIndex(0);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Failed to clear cache');
    }
  };

  const formatText = (text) => {
    // Basic markdown formatting for inline elements
    let formatted = text;
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');
    return formatted;
  };

  const renderAnalysisBlock = (block, index) => {
    // Header detection
    if (block.startsWith('####')) {
      return <h4 key={index} dangerouslySetInnerHTML={{ __html: formatText(block.replace(/^####\s*/, '')) }} />;
    }
    if (block.startsWith('###')) {
      return <h3 key={index} dangerouslySetInnerHTML={{ __html: formatText(block.replace(/^###\s*/, '')) }} />;
    }
    if (block.startsWith('##')) {
      return <h2 key={index} dangerouslySetInnerHTML={{ __html: formatText(block.replace(/^##\s*/, '')) }} />;
    }
    
    // List detection (bullet points)
    if (block.match(/^\s*[-•]\s+/m)) {
      const items = block.split(/\n/).filter(line => line.trim().match(/^\s*[-•]\s+/));
      return (
        <ul key={index}>
          {items.map((item, i) => (
            <li key={i} dangerouslySetInnerHTML={{ __html: formatText(item.replace(/^\s*[-•]\s+/, '')) }} />
          ))}
        </ul>
      );
    }

    // Numbered list detection
    if (block.match(/^\s*\d+\.\s+/m)) {
         const items = block.split(/\n/).filter(line => line.trim().match(/^\s*\d+\.\s+/));
         return (
           <ol key={index}>
             {items.map((item, i) => (
               <li key={i} dangerouslySetInnerHTML={{ __html: formatText(item.replace(/^\s*\d+\.\s+/, '')) }} />
             ))}
           </ol>
         );
    }
    
    // Standard paragraph
    return <p key={index} dangerouslySetInnerHTML={{ __html: formatText(block) }} />;
  };

  const renderAnalysis = (analysis) => {
    if (!analysis) return null;
    if (typeof analysis === 'object') {
        return <pre className="json-block">{JSON.stringify(analysis, null, 2)}</pre>;
    }
    
    // Split by double newline to identify blocks
    const blocks = analysis.split(/\n\n+/);
    
    return (
      <div className="analysis-content">
        {blocks.map((block, index) => renderAnalysisBlock(block, index))}
      </div>
    );
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopySuccess('Copied!');
      setTimeout(() => setCopySuccess(''), 2000);
    });
  };

  const updateRefinementPrompt = (index, value) => {
      setRefinementPrompts(prev => ({
          ...prev,
          [`prompt_${index}`]: value
      }));
  };

  // Format description text for better readability
  const formatDescription = (text) => {
    if (!text) return null;
    
    // Split by sentences and group into logical paragraphs
    const sentences = text.split(/\.\s+/);
    const paragraphs = [];
    let currentPara = [];
    
    sentences.forEach((sentence, idx) => {
      currentPara.push(sentence.trim());
      
      // Create new paragraph every 2-3 sentences or at natural breaks
      if (currentPara.length >= 2 || idx === sentences.length - 1) {
        if (currentPara.join('. ').trim()) {
          paragraphs.push(currentPara.join('. ') + (idx < sentences.length - 1 ? '.' : ''));
        }
        currentPara = [];
      }
    });
    
    return paragraphs.map((para, idx) => (
      <p key={idx} className="info-para">{para}</p>
    ));
  };

  return (
    <div className="app-wrapper">
      <nav className="glass-nav">
        <div className="nav-content">
          <div className="logo-section" onClick={() => window.location.reload()}>
            <div className="logo-icon-wrapper">
              <FontAwesomeIcon icon={faEye} className="app-logo" />
            </div>
            <span className="brand-name">Frame Insight</span>
          </div>
          <div className="nav-actions">
             <button 
                className="nav-link nav-btn" 
                onClick={() => setShowHistory(!showHistory)}
                title="View History"
             >
                <FontAwesomeIcon icon={faHistory} />
                <span className="nav-link-text">History</span>
                {history.length > 0 && <span className="history-badge">{history.length}</span>}
             </button>
             <a href="https://github.com/smile4fun1/video-to-prompt" target="_blank" rel="noopener noreferrer" className="nav-link">
                <FontAwesomeIcon icon={faGithub} />
             </a>
          </div>
        </div>
      </nav>

      {/* History Panel */}
      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h2><FontAwesomeIcon icon={faHistory} /> Analysis History</h2>
            <div className="history-actions">
              {history.length > 0 && (
                <button onClick={clearAllHistory} className="clear-history-btn">
                  <FontAwesomeIcon icon={faTrashAlt} /> Clear All
                </button>
              )}
              <button onClick={() => setShowHistory(false)} className="close-history-btn">×</button>
            </div>
          </div>
          <div className="history-content">
            {history.length === 0 ? (
              <div className="history-empty">
                <FontAwesomeIcon icon={faClock} className="empty-icon" />
                <p>No analysis history yet</p>
                <p className="empty-subtext">Your past analyses will appear here</p>
              </div>
            ) : (
              <div className="history-list">
                {history.map((item) => (
                  <div key={item.id} className="history-item">
                    <div className="history-item-header">
                      <div className="history-item-info">
                        <h3 className="history-filename">{item.filename}</h3>
                        <p className="history-timestamp">
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div className="history-item-actions">
                        <button 
                          onClick={() => loadFromHistory(item)} 
                          className="history-load-btn"
                          title="Load this analysis"
                        >
                          <FontAwesomeIcon icon={faEye} /> View
                        </button>
                        <button 
                          onClick={() => deleteHistoryItem(item.id)} 
                          className="history-delete-btn"
                          title="Delete this analysis"
                        >
                          <FontAwesomeIcon icon={faTrashAlt} />
                        </button>
                      </div>
                    </div>
                    <div className="history-item-meta">
                      <span className="history-badge">{item.analysisType?.replace(/_/g, ' ')}</span>
                      <span className="history-frames">{item.result?.frames_extracted || 0} frames</span>
                    </div>
                    <div className="history-preview">
                      {typeof item.result?.analysis === 'string' 
                        ? item.result.analysis.substring(0, 150) + '...' 
                        : 'Analysis completed'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <main className="main-content">
        <div className="hero-section">
            <h1>Video Intelligence, Amplified.</h1>
            <p className="subtitle">
                Analyze any video from local files or URLs. Extract KPIs, sentiment, technical data, brand insights, and more with our adaptive AI engine.
            </p>
        </div>

        <div className="control-panel glass-panel">
            <form onSubmit={handleSubmit}>
                <div className="input-type-toggle">
                    <button 
                        type="button" 
                        className={`toggle-btn ${inputType === 'file' ? 'active' : ''}`}
                        onClick={() => setInputType('file')}
                    >
                        <FontAwesomeIcon icon={faFileVideo} /> Upload File
                    </button>
                    <button 
                        type="button" 
                        className={`toggle-btn ${inputType === 'url' ? 'active' : ''}`}
                        onClick={() => setInputType('url')}
                    >
                        <FontAwesomeIcon icon={faLink} /> Video URL
                    </button>
                </div>

                <div className="input-group">
                    <label className="input-label">
                        {inputType === 'file' ? 'Video Source' : 'Video Link'}
                    </label>
                    {inputType === 'file' ? (
                        <div 
                            className={`dropzone-inline ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                            onDragEnter={handleDragEnter}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                ref={fileInputRef}
                                id="file-upload"
                                onChange={handleFileSelect}
                                accept="video/*"
                                className="file-input"
                                style={{display: 'none'}}
                            />
                            {!file ? (
                                <>
                                    <FontAwesomeIcon icon={faVideo} className="dropzone-inline-icon" />
                                    <div className="dropzone-inline-text">
                                        <p className="dropzone-main-text">
                                            {isDragging ? 'Drop video here' : 'Drag & drop your video here'}
                                        </p>
                                        <p className="dropzone-sub-text">or click to browse</p>
                                        <p className="dropzone-formats-text">Supports: MP4, MOV, AVI, WebM</p>
                                    </div>
                                </>
                            ) : (
                                <div className="file-selected">
                                    <FontAwesomeIcon icon={faCheckCircle} className="file-check-icon" />
                                    <div className="file-info">
                                        <p className="file-name">{file.name}</p>
                                        <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                    </div>
                                    <button 
                                        type="button" 
                                        className="file-remove-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setFile(null);
                                            if (fileInputRef.current) fileInputRef.current.value = '';
                                        }}
                                    >
                                        <FontAwesomeIcon icon={faTrashAlt} />
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <>
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste video URL here..."
                                className="modern-select"
                            />
                            <div className="info-box" style={{marginTop: '8px', fontSize: '13px', opacity: 0.8}}>
                                💡 <strong>Tip:</strong> If URL download fails due to platform restrictions, download the video manually and use "Upload File" for 100% reliability.
                            </div>
                        </>
                    )}
                </div>

                <div className="input-group">
                     <label className="input-label">
                        <FontAwesomeIcon icon={faCogs} className="label-icon" /> Analysis Model
                    </label>
                    <div className="select-wrapper">
                        <select
                            value={analysisType}
                            onChange={(e) => setAnalysisType(e.target.value)}
                            className="modern-select"
                        >
                            {Object.entries(analysisTypes).map(([key, value]) => (
                                <option key={key} value={key}>
                                    {key === 'auto' ? 'AUTO (Recommended)' : key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </option>
                            ))}
                        </select>
                    </div>
                    {analysisTypes[analysisType] && analysisType !== 'custom' && (
                        <div className="info-box">
                            {formatDescription(analysisTypes[analysisType])}
                        </div>
                    )}
                </div>

                {analysisType === 'custom' && (
                    <div className="input-group slide-in">
                        <label className="input-label">Custom Prompt</label>
                        <textarea
                            value={customPrompt}
                            onChange={(e) => setCustomPrompt(e.target.value)}
                            placeholder="Describe exactly what you want to extract from the video..."
                            className="modern-textarea"
                            rows="4"
                        />
                    </div>
                )}

                <div className="action-row">
                    <button type="submit" className={`primary-btn ${loading ? 'loading-btn' : ''}`} disabled={loading}>
                        {loading ? (
                            <>
                                <FontAwesomeIcon icon={faSpinner} spin /> Processing
                            </>
                        ) : (
                            <>
                                <FontAwesomeIcon icon={faUpload} /> Analyze Video
                            </>
                        )}
                    </button>
                    {!isFirstUpload && (
                         <button type="button" onClick={clearCache} className="secondary-btn">
                            <FontAwesomeIcon icon={faTrashAlt} /> Reset
                        </button>
                    )}
                </div>
            </form>

            {loading && (
                <div className="progress-section fade-in">
                    <div className="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p className="loading-text">{loadingMessages[loadingMessageIndex]}</p>
                </div>
            )}

            {error && (
                <div className="error-banner fade-in">
                    <div className="error-content">
                        <strong>Error:</strong> {error}
                    </div>
                </div>
            )}
        </div>

        {/* Original Analysis Result */}
        {result && result.analysis && (
            <div className="result-section glass-panel slide-up" ref={resultRef}>
                <div className="result-header">
                    <div className="result-title">
                        <FontAwesomeIcon icon={faChartBar} className="result-icon" />
                        <h2>Original Analysis</h2>
                    </div>
                    <div className="result-meta">
                        <span className="badge">{(result.analysis_type || analysisType)?.replace(/_/g, ' ')}</span>
                        <span className="badge secondary">{result.frames_extracted || 0} Frames</span>
                    </div>
                </div>
                
                <div className="result-body">
                    {renderAnalysis(result.analysis)}
                </div>
                
                {/* Refinement Section for Original */}
                <div className="refinement-section">
                    <h3><FontAwesomeIcon icon={faMagic} /> AI Refinement</h3>
                    <div className="refinement-input-wrapper">
                         <textarea
                            value={refinementPrompts['prompt_-1'] || ''}
                            onChange={(e) => updateRefinementPrompt(-1, e.target.value)}
                            placeholder="Ask AI to format, summarize, or extract specific details from the analysis above..."
                            className="modern-textarea refinement-textarea"
                            rows="2"
                        />
                        <button 
                            onClick={() => handleRefine(-1)} 
                            disabled={refiningIndex === -1 || !refinementPrompts['prompt_-1']?.trim()}
                            className="primary-btn refine-btn"
                        >
                             {refiningIndex === -1 ? <FontAwesomeIcon icon={faSpinner} spin /> : "Refine Result"}
                        </button>
                    </div>
                </div>

                <div className="result-actions">
                    <button onClick={() => copyToClipboard(`Analysis Type: ${result.analysis_type || analysisType}\n\n${result.analysis}`)} className="icon-btn" title="Copy to Clipboard">
                        <FontAwesomeIcon icon={faCheckCircle} style={{ opacity: copySuccess ? 1 : 0.3, marginRight: 5 }} />
                        {copySuccess || "Copy Report"}
                    </button>
                </div>
            </div>
        )}

        {/* Refined Results */}
        {refinements.map((refinement, index) => (
            <div key={index} className="result-section glass-panel slide-up refinement-card">
                <div className="result-header">
                    <div className="result-title">
                        <FontAwesomeIcon icon={faMagic} className="result-icon" />
                        <h2>Refinement {index + 1}</h2>
                    </div>
                    <div className="result-meta">
                        <span className="badge refinement-badge">{refinement.analysis_type?.replace(/_/g, ' ')}</span>
                        <span className="badge secondary">Refined</span>
                    </div>
                </div>
                
                <div className="refinement-prompt-used">
                    <small><strong>Prompt:</strong> {refinement.prompt_used}</small>
                </div>
                
                <div className="result-body">
                    {renderAnalysis(refinement.analysis)}
                </div>
                
                {/* Refinement Section for Each Refinement */}
                <div className="refinement-section">
                    <h3><FontAwesomeIcon icon={faMagic} /> Further Refine</h3>
                    <div className="refinement-input-wrapper">
                         <textarea
                            value={refinementPrompts[`prompt_${index}`] || ''}
                            onChange={(e) => updateRefinementPrompt(index, e.target.value)}
                            placeholder="Refine this result further..."
                            className="modern-textarea refinement-textarea"
                            rows="2"
                        />
                        <button 
                            onClick={() => handleRefine(index)} 
                            disabled={refiningIndex === index || !refinementPrompts[`prompt_${index}`]?.trim()}
                            className="primary-btn refine-btn"
                        >
                             {refiningIndex === index ? <FontAwesomeIcon icon={faSpinner} spin /> : "Refine Again"}
                        </button>
                    </div>
                </div>

                <div className="result-actions">
                    <button onClick={() => copyToClipboard(refinement.analysis)} className="icon-btn" title="Copy to Clipboard">
                        <FontAwesomeIcon icon={faCopy} style={{ marginRight: 5 }} />
                        Copy This
                    </button>
                </div>
            </div>
        ))}
      </main>

      <footer className="app-footer">
        <p>© {new Date().getFullYear()} Frame Insight. Engineered for precision.</p>
        <div className="social-links">
             <a href="#"><FontAwesomeIcon icon={faTwitter} /></a>
             <a href="#"><FontAwesomeIcon icon={faLinkedin} /></a>
        </div>
      </footer>
    </div>
  );
}

export default App;
