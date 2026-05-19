import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Play, Loader2, Save, X, Download, RotateCcw, Trash2 } from 'lucide-react'
import type { Job } from '../types'
import type { MediaProfile } from '../profiles'
import { loadProfiles, saveProfiles } from '../profiles'
import { ProgressPanel } from './ProgressPanel'

interface FloatingBarProps {
  onStartCompression: () => void
  compressionDisabled: boolean
  compressionLoading: boolean
  jobs: Job[]
  onCancelJob: (id: string) => void
  onDismissJob: (id: string) => void
  currentSettings: Omit<MediaProfile, 'name'>
  onApplyProfile: (settings: Omit<MediaProfile, 'name'>) => void
  onApplyDefaults: () => void
}

interface ProfileModalContentProps {
  t: TFunction
  currentSettings: Omit<MediaProfile, 'name'>
  onApplyProfile: (settings: Omit<MediaProfile, 'name'>) => void
  onApplyDefaults: () => void
}

const ProfileModalContent: React.FC<ProfileModalContentProps> = ({
  t,
  currentSettings,
  onApplyProfile,
  onApplyDefaults,
}) => {
  const [profiles, setProfiles] = useState<MediaProfile[]>(loadProfiles)
  const [profileName, setProfileName] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  const showMessage = useCallback((msg: string): void => {
    setStatusMessage(msg)
    setTimeout(() => {
      setStatusMessage('')
    }, 3000)
  }, [])

  const handleSave = (): void => {
    const name = profileName.trim()
    if (!name) {
      showMessage(t('profile.name_required'))
      return
    }
    const existingIndex = profiles.findIndex((p) => p.name === name)
    let updated: MediaProfile[]
    if (existingIndex >= 0) {
      if (!window.confirm(t('profile.overwrite_confirm', { name }))) return
      updated = [...profiles]
      updated[existingIndex] = { ...currentSettings, name }
    } else {
      updated = [...profiles, { ...currentSettings, name }]
    }
    setProfiles(updated)
    saveProfiles(updated)
    showMessage(t('profile.saved', { name }))
    setProfileName('')
  }

  const handleLoad = (profile: MediaProfile): void => {
    const { name: _name, ...settings } = profile
    onApplyProfile(settings)
    showMessage(t('profile.loaded', { name: _name }))
  }

  const handleDelete = (name: string): void => {
    const updated = profiles.filter((p) => p.name !== name)
    setProfiles(updated)
    saveProfiles(updated)
    showMessage(t('profile.deleted', { name }))
  }

  const handleDefaults = (): void => {
    onApplyDefaults()
    showMessage(t('profile.defaults_loaded'))
  }

  return (
    <div>
      <div className="profile-bar">
        <input
          type="text"
          value={profileName}
          onChange={(e) => {
            setProfileName(e.target.value)
          }}
          placeholder={t('profile.name_placeholder')}
          className="profile-name-input"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave()
          }}
        />
        <button
          className="secondary-button profile-btn"
          onClick={handleSave}
          title={t('profile.save')}
          aria-label={t('profile.save')}
        >
          <Save size={14} />
        </button>
        <button
          className="secondary-button profile-btn"
          onClick={handleDefaults}
          title={t('profile.load_defaults')}
          aria-label={t('profile.load_defaults')}
        >
          <RotateCcw size={14} />
        </button>
      </div>
      {profiles.length > 0 ? (
        <div className="profile-list">
          {profiles.map((profile) => (
            <div key={profile.name} className="profile-item">
              <span className="profile-item-name" title={profile.name}>
                {profile.name}
              </span>
              <span className="profile-item-type">
                {profile.mediaType === 'video' ? t('nav.video') : t('nav.audio')}
              </span>
              <button
                className="secondary-button profile-action-btn"
                onClick={() => {
                  handleLoad(profile)
                }}
                title={t('profile.load')}
                aria-label={t('profile.load')}
              >
                <Download size={14} />
              </button>
              <button
                className="secondary-button profile-action-btn"
                onClick={() => {
                  handleDelete(profile.name)
                }}
                title={t('profile.delete')}
                aria-label={t('profile.delete')}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p
          className="text-muted"
          style={{ fontSize: '0.9rem', textAlign: 'center', padding: '16px 0' }}
        >
          {t('profile.no_profiles')}
        </p>
      )}
      {statusMessage && (
        <div className="status-message" style={{ marginTop: '8px' }}>
          {statusMessage}
        </div>
      )}
    </div>
  )
}

const FloatingBar: React.FC<FloatingBarProps> = ({
  onStartCompression,
  compressionDisabled,
  compressionLoading,
  jobs,
  onCancelJob,
  onDismissJob,
  currentSettings,
  onApplyProfile,
  onApplyDefaults,
}) => {
  const { t } = useTranslation()
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [progressModalOpen, setProgressModalOpen] = useState(false)
  const profileModalRef = useRef<HTMLDivElement>(null)
  const progressModalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        profileModalOpen &&
        profileModalRef.current &&
        e.target instanceof Element &&
        !profileModalRef.current.contains(e.target) &&
        !e.target.closest('[data-profile-trigger]')
      ) {
        setProfileModalOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [profileModalOpen])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        progressModalOpen &&
        progressModalRef.current &&
        e.target instanceof Element &&
        !progressModalRef.current.contains(e.target) &&
        !e.target.closest('[data-progress-trigger]')
      ) {
        setProgressModalOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [progressModalOpen])

  const runningJobs = jobs.filter((j) => j.status === 'running' || j.status === 'starting')
  const hasJobs = jobs.length > 0

  const closeProfileModal = (): void => {
    setProfileModalOpen(false)
  }

  const closeProgressModal = (): void => {
    setProgressModalOpen(false)
  }

  return (
    <>
      <div className="floating-bar">
        <div className="floating-bar-left">
          <button
            className="floating-bar-btn"
            onClick={() => {
              setProfileModalOpen(!profileModalOpen)
              setProgressModalOpen(false)
            }}
            data-profile-trigger
          >
            <Save size={16} />
            <span>{t('profile.title')}</span>
          </button>

          <button
            className="floating-bar-btn"
            onClick={() => {
              setProgressModalOpen(!progressModalOpen)
              setProfileModalOpen(false)
            }}
            data-progress-trigger
          >
            {runningJobs.length > 0 ? (
              <Loader2 size={16} className="spin" />
            ) : (
              <span className="floating-bar-btn-dot" />
            )}
            <span>{t('compress.progress')}</span>
            {hasJobs && <span className="floating-bar-badge">{jobs.length}</span>}
          </button>
        </div>

        <div className="floating-bar-right">
          <button
            className="primary-button floating-bar-start-btn"
            onClick={onStartCompression}
            disabled={compressionDisabled || compressionLoading}
          >
            {compressionLoading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            {t('compress.start')}
          </button>
        </div>
      </div>

      {profileModalOpen && (
        <div className="modal-overlay" onClick={closeProfileModal}>
          <div
            className="modal-content"
            ref={profileModalRef}
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <div className="modal-header">
              <h3>
                <Save size={18} /> {t('profile.title')}
              </h3>
              <button
                className="panel-close-button"
                onClick={closeProfileModal}
                aria-label={t('common.close')}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <ProfileModalContent
                t={t}
                currentSettings={currentSettings}
                onApplyProfile={onApplyProfile}
                onApplyDefaults={onApplyDefaults}
              />
            </div>
          </div>
        </div>
      )}

      {progressModalOpen && (
        <div className="modal-overlay" onClick={closeProgressModal}>
          <div
            className="modal-content modal-content-progress"
            ref={progressModalRef}
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <div className="modal-header">
              <h3>{t('compress.progress')}</h3>
              <button
                className="panel-close-button"
                onClick={closeProgressModal}
                aria-label={t('common.close')}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              {hasJobs ? (
                <ProgressPanel
                  jobs={jobs}
                  onCancel={onCancelJob}
                  onDismiss={onDismissJob}
                  embedded
                />
              ) : (
                <div className="progress-empty">
                  <p className="text-muted">{t('profile.no_profiles')}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default FloatingBar
