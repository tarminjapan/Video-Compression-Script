import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Settings, Play, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:5000/api';

interface Progress {
  percent: number;
  current_time: number;
  total_duration: number;
  fps: number;
  speed: number;
  eta: number;
  status: string;
}

interface TaskResult {
  is_success: boolean;
  output_path: string;
  output_size: number;
  compression_ratio: number;
  error_message: string;
}

function App() {
  const [inputPath, setInputPath] = useState('');
  const [mediaInfo, setMediaInfo] = useState<any>(null);
  const [crf, setCrf] = useState(25);
  const [preset, setPreset] = useState(6);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<Progress | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);

  const fetchMediaInfo = async (path: string) => {
    try {
      const response = await axios.get(`${API_BASE}/info?path=${encodeURIComponent(path)}`);
      setMediaInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch media info', error);
      setMediaInfo(null);
    }
  };

  const startCompression = async () => {
    if (!inputPath) return;

    setStatus('starting');
    setResult(null);
    setProgress(null);

    try {
      const response = await axios.post(`${API_BASE}/compress/video`, {
        input_path: inputPath,
        crf,
        preset,
      });
      setTaskId(response.data.task_id);
      setStatus('running');
    } catch (error) {
      console.error('Failed to start compression', error);
      setStatus('error');
    }
  };

  const cancelCompression = async () => {
    if (!taskId) return;
    try {
      await axios.post(`${API_BASE}/cancel/${taskId}`);
    } catch (error) {
      console.error('Failed to cancel compression', error);
    }
  };

  useEffect(() => {
    let interval: number;

    if (taskId && (status === 'running' || status === 'starting')) {
      interval = window.setInterval(async () => {
        try {
          const response = await axios.get(`${API_BASE}/status/${taskId}`);
          const data = response.data;
          
          setStatus(data.status);
          setProgress(data.progress);
          
          if (data.status === 'success' || data.status === 'failed' || data.status === 'cancelled') {
            setResult(data.result);
            setTaskId(null);
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Failed to fetch status', error);
          clearInterval(interval);
        }
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [taskId, status]);

  return (
    <div className="container">
      <header>
        <h1>AmeCompression</h1>
        <p>Electron + React + Flask Migration</p>
      </header>

      <main>
        <section className="input-section">
          <div className="card">
            <h2><Upload size={20} /> Input File</h2>
            <div className="input-group">
              <input 
                type="text" 
                placeholder="Enter file path..." 
                value={inputPath}
                onChange={(e) => setInputPath(e.target.value)}
                onBlur={() => fetchMediaInfo(inputPath)}
              />
            </div>
            {mediaInfo && (
              <div className="media-info">
                <span>{mediaInfo.type.toUpperCase()}</span>
                {mediaInfo.width && <span>{mediaInfo.width}x{mediaInfo.height}</span>}
                {mediaInfo.duration && <span>{Math.round(mediaInfo.duration)}s</span>}
              </div>
            )}
          </div>
        </section>

        <section className="settings-section">
          <div className="card">
            <h2><Settings size={20} /> Settings</h2>
            <div className="settings-grid">
              <div className="setting-item">
                <label>CRF (Quality): {crf}</label>
                <input 
                  type="range" min="0" max="63" 
                  value={crf} 
                  onChange={(e) => setCrf(parseInt(e.target.value))}
                />
              </div>
              <div className="setting-item">
                <label>Preset (Speed): {preset}</label>
                <input 
                  type="range" min="0" max="13" 
                  value={preset} 
                  onChange={(e) => setPreset(parseInt(e.target.value))}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="action-section">
          <button 
            className="primary-button" 
            onClick={startCompression}
            disabled={!inputPath || status === 'running' || status === 'starting'}
          >
            {status === 'running' ? <Loader2 className="spin" /> : <Play size={20} />}
            Start Compression
          </button>
          
          {(status === 'running' || status === 'starting') && (
            <button className="secondary-button" onClick={cancelCompression}>
              Cancel
            </button>
          )}
        </section>

        {progress && (
          <section className="progress-section">
            <div className="card">
              <div className="progress-header">
                <span>Compressing...</span>
                <span>{Math.round(progress.percent)}%</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress.percent}%` }}></div>
              </div>
              <div className="progress-stats">
                <span>FPS: {Math.round(progress.fps)}</span>
                <span>Speed: {progress.speed.toFixed(2)}x</span>
                <span>ETA: {Math.round(progress.eta)}s</span>
              </div>
            </div>
          </section>
        )}

        {result && (
          <section className="result-section">
            <div className={`card ${result.is_success ? 'success' : 'error'}`}>
              {result.is_success ? (
                <>
                  <h3><CheckCircle size={20} /> Success!</h3>
                  <p>Reduction: {result.compression_ratio.toFixed(1)}%</p>
                  <p className="path">Output: {result.output_path}</p>
                </>
              ) : (
                <>
                  <h3><XCircle size={20} /> Failed</h3>
                  <p>{result.error_message}</p>
                </>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
