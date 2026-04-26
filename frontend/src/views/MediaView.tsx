import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Upload, Settings, Play, Loader2, Info } from 'lucide-react'
import { api, initializeApi } from '../services/api'
import type { MediaInfo } from '../types'

const MediaView: React.FC = () => {
  const { t } = useTranslation()
  const [inputPath, setInputPath] = useState('')
  const [mediaInfo, setMediaInfo] = useState<MediaInfo | null>(null)

  // Video settings
  const [crf, setCrf] = useState(25)
  const [preset, setPreset] = useState(6)
  const [maxResolution, setMaxResolution] = useState('original')
  const [maxFps, setMaxFps] = useState('unlimited')
  const [videoAudioBitrate, setVideoAudioBitrate] = useState('192k')
  const [audioEnabled, setAudioEnabled] = useState(true)

  // Audio settings
  const [audioBitrate, setAudioBitrate] = useState('192k')
  const [keepMetadata, setKeepMetadata] = useState(true)

  // Common settings
  const [volumeMode, setVolumeMode] = useState('disabled')
  const [volumeValue, setVolumeValue] = useState(0)
  const [denoiseEnabled, setDenoiseEnabled] = useState(false)
  const [denoiseLevel, setDenoiseLevel] = useState(0.15)

  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'video' | 'audio'>('video')

  const fetchMediaInfo = async (path: string) => {
    if (!path) return
    try {
      await initializeApi()
      const response = await api.get<MediaInfo>(`/media-info?path=${encodeURIComponent(path)}`)
      setMediaInfo(response.data)
      if (response.data.type === 'audio' || response.data.type === 'video') {
        setMediaType(response.data.type)
      }
    } catch (error) {
      console.error('Failed to fetch media info', error)
      setMediaInfo(null)
    }
  }

  const startCompression = async () => {
    setLoading(true)

    let volumeGain = null
    if (volumeMode === 'auto') volumeGain = 'auto'
    else if (volumeMode === 'multiplier') volumeGain = `${volumeValue}`
    else if (volumeMode === 'db') volumeGain = `${volumeValue}dB`

    try {
      if (mediaType === 'video') {
        const response = await api.post<{ task_id: string }>('/jobs/video', {
          input_path: inputPath,
          crf,
          preset,
          audio_bitrate: videoAudioBitrate,
          audio_enabled: audioEnabled,
          resolution: maxResolution === 'original' ? null : maxResolution,
          max_fps: maxFps === 'unlimited' ? null : parseInt(maxFps),
          volume_gain_db: volumeGain,
          denoise_level: denoiseEnabled ? denoiseLevel : null,
        })
        setTaskId(response.data.task_id)
      } else {
        const response = await api.post<{ task_id: string }>('/jobs/audio', {
          input_path: inputPath,
          bitrate: audioBitrate,
          keep_metadata: keepMetadata,
          volume_gain_db: volumeGain,
          denoise_level: denoiseEnabled ? denoiseLevel : null,
        })
        setTaskId(response.data.task_id)
      }
    } catch (error) {
      console.error('Failed to start compression', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.video_audio')}</h1>
        <p>
          {t('video_settings.title')} / {t('audio_settings.title')}
        </p>
      </header>

      <section className="card">
        <h2>
          <Upload size={18} /> {t('file.select')}
        </h2>
        <div className="input-group">
          <input
            type="text"
            placeholder={t('file.browse_hint')}
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            onBlur={() => void fetchMediaInfo(inputPath)}
          />
        </div>
        {mediaInfo && (
          <div className="media-info-display">
            <p>
              <strong>{t('file.format')}:</strong> {mediaInfo.type}
            </p>
            {mediaInfo.type === 'video' && (
              <p>
                <strong>{t('video_settings.resolution.original')}:</strong> {mediaInfo.width}x
                {mediaInfo.height}
              </p>
            )}
            {mediaInfo.type === 'audio' && (
              <p>
                <strong>{t('audio_settings.bitrate')}:</strong>{' '}
                {mediaInfo.bitrate ? `${Math.round(mediaInfo.bitrate / 1000)}kbps` : 'Unknown'}
              </p>
            )}
            <p>
              <strong>{t('file.duration')}:</strong> {Math.round(mediaInfo.duration)}s
            </p>
          </div>
        )}
        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'inline-block', marginRight: '16px' }}>
            <input
              type="radio"
              checked={mediaType === 'video'}
              onChange={() => setMediaType('video')}
            />{' '}
            {t('nav.video')}
          </label>
          <label style={{ display: 'inline-block' }}>
            <input
              type="radio"
              checked={mediaType === 'audio'}
              onChange={() => setMediaType('audio')}
            />{' '}
            {t('nav.audio')}
          </label>
        </div>
      </section>

      <section className="card">
        <h2>
          <Settings size={18} />{' '}
          {mediaType === 'video' ? t('video_settings.title') : t('audio_settings.title')}
        </h2>

        {mediaType === 'video' ? (
          <>
            <div className="section-title">{t('video_settings.video_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>
                  {t('video_settings.crf')}: {crf}
                </label>
                <input
                  type="range"
                  min="0"
                  max="63"
                  value={crf}
                  onChange={(e) => setCrf(parseInt(e.target.value))}
                />
                <small>{t('video_settings.crf_range')}</small>
              </div>
              <div className="setting-item">
                <label>
                  {t('video_settings.preset')}: {preset}
                </label>
                <input
                  type="range"
                  min="0"
                  max="13"
                  value={preset}
                  onChange={(e) => setPreset(parseInt(e.target.value))}
                />
                <small>{t('video_settings.preset_range')}</small>
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_resolution')}</label>
                <select value={maxResolution} onChange={(e) => setMaxResolution(e.target.value)}>
                  <option value="original">{t('video_settings.resolution.original')}</option>
                  <option value="3840x2160">{t('video_settings.resolution.4k')}</option>
                  <option value="1920x1080">{t('video_settings.resolution.1080p')}</option>
                  <option value="1280x720">{t('video_settings.resolution.720p')}</option>
                  <option value="854x480">{t('video_settings.resolution.480p')}</option>
                </select>
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_fps')}</label>
                <select value={maxFps} onChange={(e) => setMaxFps(e.target.value)}>
                  <option value="unlimited">{t('video_settings.fps_options.unlimited')}</option>
                  <option value="60">60 FPS</option>
                  <option value="30">30 FPS</option>
                  <option value="24">24 FPS</option>
                </select>
              </div>
            </div>

            <div className="section-title">{t('video_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('video_settings.audio_bitrate')}</label>
                <select
                  value={videoAudioBitrate}
                  onChange={(e) => setVideoAudioBitrate(e.target.value)}
                  disabled={!audioEnabled}
                >
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
                    checked={!audioEnabled}
                    onChange={(e) => setAudioEnabled(!e.target.checked)}
                  />{' '}
                  {t('video_settings.disable_audio')}
                </label>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('audio_settings.bitrate')}</label>
                <select value={audioBitrate} onChange={(e) => setAudioBitrate(e.target.value)}>
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
                  />{' '}
                  {t('audio_settings.keep_metadata')}
                </label>
              </div>
            </div>
          </>
        )}

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
                {volumeValue}
                {volumeMode === 'db' ? ' dB' : 'x'}
              </label>
              <input
                type="range"
                min={volumeMode === 'multiplier' ? '0.1' : '-20'}
                max={volumeMode === 'multiplier' ? '5.0' : '20'}
                step={volumeMode === 'multiplier' ? '0.1' : '1'}
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
              />{' '}
              {t('denoise.enable')}
            </label>
          </div>
          {denoiseEnabled && (
            <div className="setting-item">
              <label>
                {t('denoise.level')}: {denoiseLevel}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
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
          onClick={() => void startCompression()}
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
  )
}

export default MediaView
