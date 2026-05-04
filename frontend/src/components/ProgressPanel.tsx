import React from 'react'
import { useTranslation } from 'react-i18next'
import { X, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import type { Job } from '../types'

interface ProgressPanelProps {
  jobs: Job[]
  onCancel: (id: string) => void
}

function formatTime(seconds: number): string {
  if (!seconds || seconds <= 0 || !isFinite(seconds)) return '--:--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatTimeShort(seconds: number): string {
  if (!seconds || seconds <= 0 || !isFinite(seconds)) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({ jobs, onCancel }) => {
  const { t } = useTranslation()

  if (jobs.length === 0) return null

  return (
    <div className="progress-panel">
      <h3>{t('compress.progress')}</h3>
      <div className="job-list">
        {jobs.map((job) => (
          <div key={job.id} className={`job-item ${job.status}`}>
            <div className="job-info">
              <span className="job-type">{job.type === 'video' ? 'Video' : 'Audio'}</span>
              <span className="job-id">ID: {job.id.substring(0, 8)}</span>
              <span className={`job-status-badge ${job.status}`}>
                {job.status === 'running' && <Loader2 size={14} className="spin" />}
                {job.status === 'success' && <CheckCircle size={14} />}
                {job.status === 'failed' && <XCircle size={14} />}
                {job.status}
              </span>
            </div>

            {job.status === 'running' && job.progress && (
              <div className="job-progress">
                <div className="progress-bar-wrapper">
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.min(100, job.progress.percent)}%` }}
                    ></div>
                  </div>
                  <span className="progress-percent">{Math.round(job.progress.percent)}%</span>
                </div>
                <div className="job-stats">
                  <span className="stat-item">
                    <span className="stat-label">{t('compress.eta')}:</span>
                    <span className="stat-value">{formatTimeShort(job.progress.eta) || '---'}</span>
                  </span>
                  {job.progress.speed !== undefined && job.progress.speed > 0 && (
                    <span className="stat-item">
                      <span className="stat-label">{t('compress.speed')}:</span>
                      <span className="stat-value">{job.progress.speed.toFixed(1)}x</span>
                    </span>
                  )}
                  {job.progress.fps !== undefined && job.progress.fps > 0 && (
                    <span className="stat-item">
                      <span className="stat-label">{t('compress.fps')}:</span>
                      <span className="stat-value">{Math.round(job.progress.fps)}</span>
                    </span>
                  )}
                </div>
                <div className="job-stats secondary-stats">
                  {job.progress.current_time !== undefined &&
                    job.progress.current_time > 0 &&
                    job.progress.total_duration !== undefined &&
                    job.progress.total_duration > 0 && (
                      <span className="stat-item">
                        <span className="stat-label">{t('compress.time_position')}:</span>
                        <span className="stat-value">
                          {formatTime(job.progress.current_time)} /{' '}
                          {formatTime(job.progress.total_duration)}
                        </span>
                      </span>
                    )}
                  {job.progress.frame !== undefined && job.progress.frame > 0 && (
                    <span className="stat-item">
                      <span className="stat-label">{t('compress.frame')}:</span>
                      <span className="stat-value">{job.progress.frame.toLocaleString()}</span>
                    </span>
                  )}
                </div>
              </div>
            )}

            {job.status === 'success' && job.result && (
              <div className="job-result">
                <span className="result-compression">
                  -{job.result.compression_ratio?.toFixed(1)}%
                </span>
              </div>
            )}

            {(job.status === 'running' || job.status === 'starting') && (
              <button
                className="cancel-button"
                onClick={() => {
                  onCancel(job.id)
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProgressPanel
