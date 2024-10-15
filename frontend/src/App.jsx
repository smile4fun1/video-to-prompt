import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks

function App() {
  const [file, setFile] = useState(null);
  const [analysisType, setAnalysisType] = useState('general');
  const [customPrompt, setCustomPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [analysisTypes, setAnalysisTypes] = useState({});

  useEffect(() => {
    fetchAnalysisTypes();
  }, []);

  const fetchAnalysisTypes = async () => {
    try {
      const response = await axios.get('http://localhost:8000/analysis_types');
      setAnalysisTypes(response.data);
    } catch (error) {
      console.error('Error fetching analysis types:', error);
    }
  };

  const uploadChunk = async (chunk, chunkNumber, totalChunks) => {
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_number', chunkNumber);
    formData.append('total_chunks', totalChunks);
    formData.append('analysis_type', analysisType);
    formData.append('custom_prompt', customPrompt);

    const response = await axios.post('http://localhost:8000/upload_chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return response.data;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a video file.');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(0);
    setResult(null);

    try {
      if (file.size <= CHUNK_SIZE) {
        // Small file, upload in one go
        const formData = new FormData();
        formData.append('file', file);
        formData.append('analysis_type', analysisType);
        formData.append('custom_prompt', customPrompt);
        const response = await axios.post('http://localhost:8000/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        setResult(response.data);
      } else {
        // Large file, use chunked upload
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        let combinedResult = [];

        for (let chunkNumber = 1; chunkNumber <= totalChunks; chunkNumber++) {
          const start = (chunkNumber - 1) * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          const chunk = file.slice(start, end);

          const chunkResult = await uploadChunk(chunk, chunkNumber, totalChunks);
          combinedResult.push(chunkResult);

          setProgress((chunkNumber / totalChunks) * 100);
        }

        setResult({
          filename: file.name,
          analysis_type: analysisType,
          custom_prompt: customPrompt,
          message: "Video processed successfully",
          chunks: combinedResult
        });
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setError('An error occurred while processing the video. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format) => {
    try {
      const response = await axios.get(`http://localhost:8000/download/${format}/${result.cache_key}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_result.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error(`Error downloading ${format} file:`, error);
      setError(`An error occurred while downloading the ${format} file. Please try again.`);
    }
  };

  return (
    <div className="app-container">
      <h1>Video Analysis App</h1>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="file-upload">Select Video File:</label>
          <input
            id="file-upload"
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            accept="video/*"
          />
        </div>
        <div className="form-group">
          <label htmlFor="analysis-type">Select Analysis Type:</label>
          <select
            id="analysis-type"
            value={analysisType}
            onChange={(e) => setAnalysisType(e.target.value)}
          >
            {Object.entries(analysisTypes).map(([key, value]) => (
              <option key={key} value={key}>{value}</option>
            ))}
          </select>
        </div>
        {analysisType === 'custom' && (
          <div className="form-group">
            <label htmlFor="custom-prompt">Custom Prompt:</label>
            <input
              id="custom-prompt"
              type="text"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Enter your custom analysis prompt"
            />
          </div>
        )}
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Upload and Analyze'}
        </button>
      </form>
      {loading && (
        <div className="loading">
          <p>Processing video, please wait...</p>
          <progress value={progress} max="100"></progress>
          <p>{Math.round(progress)}% complete</p>
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result-container">
          <h2>Analysis Result</h2>
          <p><strong>Filename:</strong> {result.filename}</p>
          <p><strong>Analysis Type:</strong> {result.analysis_type}</p>
          {result.custom_prompt && <p><strong>Custom Prompt:</strong> {result.custom_prompt}</p>}
          {result.chunks ? (
            result.chunks.map((chunk, index) => (
              <div key={index}>
                <h3>Chunk {chunk.chunk_number} of {chunk.total_chunks}</h3>
                <p><strong>Frames extracted:</strong> {chunk.frames_extracted}</p>
                <h4>GPT-4 Analysis:</h4>
                <pre className="analysis-result">{JSON.stringify(chunk.analysis, null, 2)}</pre>
              </div>
            ))
          ) : (
            <>
              <p><strong>Frames extracted:</strong> {result.frames_extracted}</p>
              <h3>GPT-4 Analysis:</h3>
              <pre className="analysis-result">{JSON.stringify(result.analysis, null, 2)}</pre>
            </>
          )}
          <div className="download-buttons">
            <button onClick={() => handleDownload('json')}>Download JSON</button>
            <button onClick={() => handleDownload('pdf')}>Download PDF</button>
            <button onClick={() => handleDownload('markdown')}>Download Markdown</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
