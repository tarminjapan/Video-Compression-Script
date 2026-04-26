import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import Layout from './components/Layout'
import MediaView from './views/MediaView'
import SettingsView from './views/SettingsView'
import ProgressPanel from './components/ProgressPanel'
import { useJobs } from './hooks/useJobs'
import { api, initializeApi } from './services/api'
import './App.css'

function App() {
  const { i18n } = useTranslation()
  const [activeView, setActiveView] = useState('media')
  const [isReady, setIsReady] = useState(false)
  const { jobs, cancelJob } = useJobs()

  useEffect(() => {
    // Initial settings fetch to apply theme and language
    const initApp = async () => {
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

  const renderView = () => {
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
      <ProgressPanel jobs={jobs} onCancel={(id) => void cancelJob(id)} />
    </>
  )
}

export default App
