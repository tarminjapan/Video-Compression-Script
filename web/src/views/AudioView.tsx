import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, Settings, Play, Loader2, Info } from 'lucide-react';
import axios from 'axios';
import type { MediaInfo } from '../types';

const API_BASE = 'http://localhost:5000/api';

const AudioView: React.FC = () => {
  const { t } = useTranslation();
  const [inputPath, setInputPath] = useState('');
  const [mediaInfo, setMediaInfo] = useState<MediaInfo | null>(null);
  const [bitrate, setBitrate] = useState('192k');
  const [keepMetadata, setKeepMetadata] = useState(true);
  const [volumeMode, setVolumeMode] = useState('disabled');
  const [volumeValue, setVolumeValue] = useState(0);
  const [denoiseEnabled, setDenoiseEnabled] = useState(false);
  const [denoiseLevel, setDenoiseLevel] = useState(0.15);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const fetchMediaInfo = async (path: string) => {
    if (!path) return;
    try {
      const response = await axios.get<MediaInfo>(`${API_BASE}/media-info?path=${encodeURIComponent(path)}`);
      setMediaInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch media info', error);
      setMediaInfo(null);
    }
  };

  const startCompression = async () => {
    setLoading(true);

    let volumeGain = null;
    if (volumeMode === 'auto') volumeGain = 'auto';
    else if (volumeMode === 'multiplier') volumeGain = `${volumeValue}`;
    else if (volumeMode === 'db') volumeGain = `${volumeValue}dB`;

    try {
      const response = await axios.post<{ task_id: string }>(`${API_BASE}/jobs/audio`, {
        input_path: inputPath,
        bitrate,
        keep_metadata: keepMetadata,
        volume_gain_db: volumeGain,
        denoise_level: denoiseEnabled ? denoiseLevel : null,
      });
      setTaskId(response.data.task_id);
    } catch (error) {
      console.error('Failed to start compression', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.audio')}</h1>
        <p>{t('audio_settings.title')}</p>
      </header>

      <section className="card">
        <h2><Upload size={18} /> {t('file.select')}</h2>
        <div className="input-group">
          <input 
            type="text" 
            placeholder={t('file.browse_hint')}
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            onBlur={() => fetchMediaInfo(inputPath)}
          />
        </div>
        {mediaInfo && (
          <div className="media-info-display">
            <p><strong>{t('file.format')}:</strong> {mediaInfo.type}</p>
            <p><strong>{t('audio_settings.bitrate')}:</strong> {mediaInfo.bitrate ? `${Math.round(mediaInfo.bitrate / 1000)}kbps` : 'Unknown'}</p>
            <p><strong>{t('file.duration')}:</strong> {Math.round(mediaInfo.duration)}s</p>
          </div>
        )}
      </section>

      <section className="card">
        <h2><Settings size={18} /> {t('audio_settings.title')}</h2>
        
        <div className="settings-grid">
          <div className="setting-item">
            <label>{t('audio_settings.bitrate')}</label>
            <select value={bitrate} onChange={(e) => setBitrate(e.target.value)}>
              <option value="64k">64k</option>
              <option value="128k">128k</option>
              <option value="192k">192k</option>
              <option value="256k">256k</option>
              <option value="320k">320k</option>
            </select>
          </div>
          <div className="setting-item">
            <label>
              <input 
                type="checkbox" 
                checked={keepMetadata} 
                onChange={(e) => setKeepMetadata(e.target.checked)} 
              />
              {' '}{t('audio_settings.keep_metadata')}
            </label>
          </div>
        </div>

        <div className="section-title">{t('volume.title')}</div>
        <div className="settings-grid">
          <div className="setting-item">
            <label>{t('volume.mode')}</label>
            <select value={volumeMode} onChange={(e) => setVolumeMode(e.target.value)}>
              <option value="disabled">{t('volume.modes.disabled')}</option>
              <option value="auto">{t('volume.modes.auto')}</option>
              <option value="multiplier">{t('volume.modes.multiplier')}</option>
              <option value="db">{t('volume.modes.db')}</option>
            </select>
          </div>
          {(volumeMode === 'multiplier' || volumeMode === 'db') && (
            <div className="setting-item">
              <label>
                {volumeMode === 'multiplier' ? t('volume.multiplier_label') : t('volume.db_label')}: 
                {volumeValue}{volumeMode === 'db' ? ' dB' : 'x'}
              </label>
              <input 
                type="range" 
                min={volumeMode === 'multiplier' ? "0.1" : "-20"} 
                max={volumeMode === 'multiplier' ? "5.0" : "20"} 
                step={volumeMode === 'multiplier' ? "0.1" : "1"}
                value={volumeValue} 
                onChange={(e) => setVolumeValue(parseFloat(e.target.value))}
              />
            </div>
          )}
        </div>

        <div className="section-title">{t('denoise.title')}</div>
        <div className="settings-grid">
          <div className="setting-item">
            <label>
              <input 
                type="checkbox" 
                checked={denoiseEnabled} 
                onChange={(e) => setDenoiseEnabled(e.target.checked)} 
              />
              {' '}{t('denoise.enable')}
            </label>
          </div>
          {denoiseEnabled && (
            <div className="setting-item">
              <label>{t('denoise.level')}: {denoiseLevel}</label>
              <input 
                type="range" min="0" max="1" step="0.01"
                value={denoiseLevel} 
                onChange={(e) => setDenoiseLevel(parseFloat(e.target.value))}
              />
            </div>
          )}
        </div>
      </section>

      <section className="action-area">
        <button 
          className="primary-button" 
          onClick={startCompression}
          disabled={!inputPath || loading}
        >
          {loading ? <Loader2 className="spin" /> : <Play size={18} />}
          {t('compress.start')}
        </button>
      </section>

      {taskId && (
         <div className="task-status-hint">
            <Info size={16} /> {t('status.processing')} (ID: {taskId})
         </div>
      )}
    </div>
  );
};

export default AudioView;
