import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Upload, Settings, Play, Loader2, Info, FileSearch, ChevronDown } from 'lucide-react'
import { api, initializeApi } from '../services/api'
import type { MediaInfo } from '../types'

const AUDIO_BITRATE_OPTIONS = [
  '16',
  '24',
  '32',
  '40',
  '48',
  '64',
  '96',
  '128',
  '160',
  '192',
  '256',
  '320',
]
const FPS_OPTIONS = ['240', '144', '120', '90', '60', '50', '48', '30', '25', '24', '20', '12']
const BITRATE_REGEX = /^\d+$/

interface ComboBoxProps {
  value: string
  onChange: (val: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  disabled?: boolean
}

const ComboBox: React.FC<ComboBoxProps> = ({ value, onChange, options, placeholder, disabled }) => {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        containerRef.current &&
        e.target instanceof Element &&
        !containerRef.current.contains(e.target)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return (): void => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(e) => {
            onChange(e.target.value)
          }}
          style={{ flex: 1, borderRadius: '4px 0 0 4px' }}
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
        />
        <button
          type="button"
          className="secondary-button"
          disabled={disabled}
          onClick={() => {
            setOpen(!open)
          }}
          style={{
            borderRadius: '0 4px 4px 0',
            padding: '0 8px',
            borderLeft: 'none',
            minWidth: '32px',
          }}
          aria-label="Toggle dropdown"
        >
          <ChevronDown size={14} />
        </button>
      </div>
      {open && (
        <ul
          role="listbox"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 1000,
            listStyle: 'none',
            margin: 0,
            padding: 0,
            maxHeight: '200px',
            overflowY: 'auto',
            background: 'var(--card-bg)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}
        >
          {options.map((opt) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={value === opt.value}
              onClick={(): void => {
                onChange(opt.value)
                setOpen(false)
              }}
              className="combobox-option"
              style={{
                padding: '6px 10px',
                cursor: 'pointer',
                background: value === opt.value ? 'var(--primary-color)' : 'transparent',
                color: value === opt.value ? '#fff' : 'inherit',
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

interface AudioSettingsSectionProps {
  t: TFunction
  volumeMode: string
  setVolumeMode: (val: string) => void
  volumeValue: number
  setVolumeValue: (val: number) => void
  denoiseEnabled: boolean
  setDenoiseEnabled: (val: boolean) => void
  denoiseLevel: number
  setDenoiseLevel: (val: number) => void
}

const AudioSettingsSection: React.FC<AudioSettingsSectionProps> = ({
  t,
  volumeMode,
  setVolumeMode,
  volumeValue,
  setVolumeValue,
  denoiseEnabled,
  setDenoiseEnabled,
  denoiseLevel,
  setDenoiseLevel,
}) => (
  <>
    <div className="sub-section-title">{t('volume.title')}</div>
    <div className="settings-grid">
      <div className="setting-item">
        <label>{t('volume.mode')}</label>
        <select
          value={volumeMode}
          onChange={(e) => {
            setVolumeMode(e.target.value)
          }}
        >
          <option value="disabled">{t('volume.modes.disabled')}</option>
          <option value="auto">{t('volume.modes.auto')}</option>
          <option value="multiplier">{t('volume.modes.multiplier')}</option>
          <option value="db">{t('volume.modes.db')}</option>
        </select>
      </div>
      {(volumeMode === 'multiplier' || volumeMode === 'db') && (
        <div className="setting-item">
          <label>
            {volumeMode === 'multiplier' ? t('volume.multiplier_label') : t('volume.db_label')}:{' '}
            {volumeValue}
            {volumeMode === 'db' ? ' dB' : 'x'}
          </label>
          <input
            type="range"
            min={volumeMode === 'multiplier' ? '0.1' : '-20'}
            max={volumeMode === 'multiplier' ? '5.0' : '20'}
            step={volumeMode === 'multiplier' ? '0.1' : '1'}
            value={volumeValue}
            onChange={(e) => {
              setVolumeValue(parseFloat(e.target.value))
            }}
          />
        </div>
      )}
    </div>

    <div className="sub-section-title">{t('denoise.title')}</div>
    <div className="settings-grid">
      <div className="setting-item">
        <label>
          <input
            type="checkbox"
            checked={denoiseEnabled}
            onChange={(e) => {
              setDenoiseEnabled(e.target.checked)
            }}
          />{' '}
          {t('denoise.enable')}
        </label>
      </div>
      {denoiseEnabled && (
        <div className="setting-item" style={{ gridColumn: 'span 2' }}>
          <label>
            {t('denoise.level')}: {denoiseLevel}
          </label>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <button
              className={`secondary-button ${denoiseLevel === 0.15 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.15)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.light')}
            </button>
            <button
              className={`secondary-button ${denoiseLevel === 0.4 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.4)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.medium')}
            </button>
            <button
              className={`secondary-button ${denoiseLevel === 0.7 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.7)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.strong')}
            </button>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={denoiseLevel}
            onChange={(e) => {
              setDenoiseLevel(parseFloat(e.target.value))
            }}
          />
        </div>
      )}
    </div>
  </>
)

const MediaView: React.FC = () => {
  const { t } = useTranslation()
  const [inputPath, setInputPath] = useState('')
  const [mediaInfo, setMediaInfo] = useState<MediaInfo | null>(null)

  // Video settings
  const [crf, setCrf] = useState(25)
  const [preset, setPreset] = useState(6)
  const [maxResolution, setMaxResolution] = useState('original')
  const [customWidth, setCustomWidth] = useState('')
  const [customHeight, setCustomHeight] = useState('')
  const [maxFps, setMaxFps] = useState('unlimited')
  const [videoAudioBitrate, setVideoAudioBitrate] = useState('192')
  const [audioEnabled, setAudioEnabled] = useState(true)

  // Audio settings
  const [audioBitrate, setAudioBitrate] = useState('192')
  const [keepMetadata, setKeepMetadata] = useState(true)

  // Common settings
  const [volumeMode, setVolumeMode] = useState('disabled')
  const [volumeValue, setVolumeValue] = useState(0)
  const [denoiseEnabled, setDenoiseEnabled] = useState(false)
  const [denoiseLevel, setDenoiseLevel] = useState(0.15)

  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'video' | 'audio'>('video')
  const [isDragging, setIsDragging] = useState(false)

  const fetchMediaInfo = useCallback(async (path: string) => {
    if (!path) return
    try {
      await initializeApi()
      const response = await api.get<MediaInfo>(`/media-info?path=${encodeURIComponent(path)}`)
      setMediaInfo(response.data)
      setMediaType(response.data.type)
    } catch (error) {
      console.error('Failed to fetch media info', error)
      setMediaInfo(null)
    }
  }, [])

  const handleSelectFile = async (): Promise<void> => {
    if (!window.electronAPI) return
    const path = await window.electronAPI.selectFile()
    if (path) {
      setInputPath(path)
      void fetchMediaInfo(path)
    }
  }

  const handleDragOver = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'copy'
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    const file = files[0]
    if (file) {
      const path = window.electronAPI?.getPathForFile?.(file) ?? file.path ?? ''

      if (path) {
        setInputPath(path)
        void fetchMediaInfo(path)
      }
    }
  }

  useEffect(() => {
    const preventDefault = (e: DragEvent): void => {
      e.preventDefault()
    }
    window.addEventListener('dragover', preventDefault)
    window.addEventListener('drop', preventDefault)
    return () => {
      window.removeEventListener('dragover', preventDefault)
      window.removeEventListener('drop', preventDefault)
    }
  }, [])

  const startCompression = async (): Promise<void> => {
    setLoading(true)

    let volumeGain = null
    if (volumeMode === 'auto') volumeGain = 'auto'
    else if (volumeMode === 'multiplier') volumeGain = `${volumeValue}`
    else if (volumeMode === 'db') volumeGain = `${volumeValue}dB`

    let resolution = maxResolution
    if (maxResolution === 'custom' && customWidth && customHeight) {
      resolution = `${customWidth}x${customHeight}`
    }

    const resolvedVideoAudioBitrate = BITRATE_REGEX.test(videoAudioBitrate)
      ? videoAudioBitrate + 'k'
      : '192k'
    const resolvedAudioBitrate = BITRATE_REGEX.test(audioBitrate) ? audioBitrate + 'k' : '192k'

    try {
      if (mediaType === 'video') {
        const response = await api.post<{ task_id: string }>('/jobs/video', {
          input_path: inputPath,
          crf,
          preset,
          audio_bitrate: resolvedVideoAudioBitrate,
          audio_enabled: audioEnabled,
          resolution: resolution === 'original' ? null : resolution,
          max_fps: maxFps === 'unlimited' ? null : parseInt(maxFps),
          volume_gain_db: volumeGain,
          denoise_level: denoiseEnabled ? denoiseLevel : null,
        })
        setTaskId(response.data.task_id)
      } else {
        const response = await api.post<{ task_id: string }>('/jobs/audio', {
          input_path: inputPath,
          bitrate: resolvedAudioBitrate,
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

      <section
        className={`card drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <h2>
          <Upload size={18} /> {t('file.select')}
        </h2>
        <div className="input-with-button">
          <input
            type="text"
            placeholder={t('file.browse_hint')}
            value={inputPath}
            onChange={(e) => {
              setInputPath(e.target.value)
            }}
            onBlur={() => void fetchMediaInfo(inputPath)}
          />
          <button className="secondary-button" onClick={() => void handleSelectFile()}>
            <FileSearch size={18} />
          </button>
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
              onChange={() => {
                setMediaType('video')
              }}
            />{' '}
            {t('nav.video')}
          </label>
          <label style={{ display: 'inline-block' }}>
            <input
              type="radio"
              checked={mediaType === 'audio'}
              onChange={() => {
                setMediaType('audio')
              }}
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
                  onChange={(e) => {
                    setCrf(parseInt(e.target.value))
                  }}
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
                  onChange={(e) => {
                    setPreset(parseInt(e.target.value))
                  }}
                />
                <small>{t('video_settings.preset_range')}</small>
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_resolution')}</label>
                <select
                  value={maxResolution}
                  onChange={(e) => {
                    setMaxResolution(e.target.value)
                  }}
                >
                  <option value="original">{t('video_settings.resolution.original')}</option>
                  <option value="3840x2160">{t('video_settings.resolution.4k')}</option>
                  <option value="1920x1080">{t('video_settings.resolution.1080p')}</option>
                  <option value="1280x720">{t('video_settings.resolution.720p')}</option>
                  <option value="854x480">{t('video_settings.resolution.480p')}</option>
                  <option value="custom">{t('video_settings.resolution.custom')}</option>
                </select>
                {maxResolution === 'custom' && (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    <input
                      type="number"
                      placeholder="W"
                      value={customWidth}
                      onChange={(e) => {
                        setCustomWidth(e.target.value)
                      }}
                    />
                    <input
                      type="number"
                      placeholder="H"
                      value={customHeight}
                      onChange={(e) => {
                        setCustomHeight(e.target.value)
                      }}
                    />
                  </div>
                )}
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_fps')}</label>
                <ComboBox
                  value={maxFps === 'unlimited' ? '' : maxFps}
                  onChange={(val) => {
                    setMaxFps(val || 'unlimited')
                  }}
                  placeholder={t('video_settings.fps_options.unlimited')}
                  options={FPS_OPTIONS.map((fps) => ({
                    value: fps,
                    label: t('video_settings.fps_options.' + fps, fps + ' FPS'),
                  }))}
                />
              </div>
            </div>

            <div className="section-title">{t('video_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('video_settings.audio_bitrate')}</label>
                <ComboBox
                  value={videoAudioBitrate}
                  onChange={(val) => {
                    setVideoAudioBitrate(BITRATE_REGEX.test(val) ? val : '192')
                  }}
                  placeholder="e.g. 192"
                  disabled={!audioEnabled}
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={!audioEnabled}
                    onChange={(e) => {
                      setAudioEnabled(!e.target.checked)
                    }}
                  />{' '}
                  {t('video_settings.disable_audio')}
                </label>
              </div>
            </div>
            <AudioSettingsSection
              t={t}
              volumeMode={volumeMode}
              setVolumeMode={setVolumeMode}
              volumeValue={volumeValue}
              setVolumeValue={setVolumeValue}
              denoiseEnabled={denoiseEnabled}
              setDenoiseEnabled={setDenoiseEnabled}
              denoiseLevel={denoiseLevel}
              setDenoiseLevel={setDenoiseLevel}
            />
          </>
        ) : (
          <>
            <div className="section-title">{t('audio_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('audio_settings.bitrate')}</label>
                <ComboBox
                  value={audioBitrate}
                  onChange={(val) => {
                    setAudioBitrate(BITRATE_REGEX.test(val) ? val : '192')
                  }}
                  placeholder="e.g. 192"
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={keepMetadata}
                    onChange={(e) => {
                      setKeepMetadata(e.target.checked)
                    }}
                  />{' '}
                  {t('audio_settings.keep_metadata')}
                </label>
              </div>
            </div>
            <AudioSettingsSection
              t={t}
              volumeMode={volumeMode}
              setVolumeMode={setVolumeMode}
              volumeValue={volumeValue}
              setVolumeValue={setVolumeValue}
              denoiseEnabled={denoiseEnabled}
              setDenoiseEnabled={setDenoiseEnabled}
              denoiseLevel={denoiseLevel}
              setDenoiseLevel={setDenoiseLevel}
            />
          </>
        )}
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
