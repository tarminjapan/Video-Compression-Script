import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import Layout from './components/Layout'
import MediaView from './views/MediaView'
import SettingsView from './views/SettingsView'
import ProgressPanel from './components/ProgressPanel'
import { useJobs } from './hooks/useJobs'
import { api, initializeApi } from './services/api'
import './App.css'

function App(): React.JSX.Element {
  const { i18n } = useTranslation()
  const [activeView, setActiveView] = useState('media')
  const [isReady, setIsReady] = useState(false)
  const { jobs, cancelJob } = useJobs()
  const [dismissedJobIds, setDismissedJobIds] = useState<Set<string>>(new Set())

  const visibleJobs = jobs.filter((job) => !dismissedJobIds.has(job.id))

  const handleDismissJob = (id: string): void => {
    setDismissedJobIds((prev) => {
      const next = new Set(prev)
      next.add(id)
      return next
    })
  }

  const cleanupDismissed = useCallback(() => {
    setDismissedJobIds((prev) => {
      if (prev.size === 0) return prev
      const currentJobIds = new Set(jobs.map((job) => job.id))
      const next = new Set<string>()
      for (const id of prev) {
        if (currentJobIds.has(id)) {
          next.add(id)
        }
      }
      if (next.size === prev.size) return prev
      return next
    })
  }, [jobs])

  useEffect(() => {
    cleanupDismissed()
  }, [cleanupDismissed])

  useEffect(() => {
    // Initial settings fetch to apply theme and language
    const initApp = async (): Promise<void> => {
      try {
        await initializeApi()

        const response = await api.get('/settings')
        const { language, appearance_mode } = response.data

        if (language) {
          void i18n.changeLanguage(language)
        }

        if (appearance_mode) {
          document.documentElement.setAttribute('data-theme', appearance_mode)
        }
      } catch (error) {
        console.error('Failed to initialize app settings', error)
      } finally {
        setIsReady(true)
      }
    }

    void initApp()
  }, [i18n])

  if (!isReady) {
    return <div className="loading-screen">Loading...</div>
  }

  const renderView = (): React.JSX.Element => {
    switch (activeView) {
      case 'media':
        return <MediaView />
      case 'settings':
        return <SettingsView />
      default:
        return (
          <div className="view-container">
            <h1>Coming Soon</h1>
            <p>This view is under development.</p>
          </div>
        )
    }
  }

  return (
    <>
      <Layout activeView={activeView} onViewChange={setActiveView}>
        {renderView()}
      </Layout>
      <ProgressPanel
        jobs={visibleJobs}
        onCancel={(id) => void cancelJob(id)}
        onDismiss={handleDismissJob}
      />
    </>
  )
}

export default App
