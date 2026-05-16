import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { api, initializeApi } from '../services/api'
import type { Job } from '../types'

export const useJobs = (): {
  jobs: Job[]
  cancelJob: (taskId: string) => Promise<void>
} => {
  const [jobs, setJobs] = useState<Job[]>([])
  const prevJobsRef = useRef<Map<string, string>>(new Map())
  const { t } = useTranslation()

  const sendNotification = useCallback((title: string, body: string) => {
    void window.electronAPI?.sendNotification(title, body)
  }, [])

  const fetchJobs = useCallback(async () => {
    try {
      await initializeApi()
      const response = await api.get<Job[]>('/jobs')
      const newJobs = response.data

      const prevMap = prevJobsRef.current
      const newMap = new Map<string, string>()
      for (const job of newJobs) {
        newMap.set(job.id, job.status)

        const prevStatus = prevMap.get(job.id)
        if (prevStatus && prevStatus !== job.status) {
          const wasRunning =
            prevStatus === 'running' || prevStatus === 'pending' || prevStatus === 'starting'
          if (wasRunning && job.status === 'success') {
            sendNotification(
              t('compress.complete'),
              t('notification.success_body', { type: t('nav.' + job.type) }),
            )
          } else if (wasRunning && job.status === 'failed') {
            sendNotification(
              t('compress.failed'),
              t('notification.failed_body', { type: t('nav.' + job.type) }),
            )
          }
        }
      }
      prevJobsRef.current = newMap
      setJobs(newJobs)
    } catch (error) {
      console.error('Failed to fetch jobs', error)
    }
  }, [t, sendNotification])

  useEffect(() => {
    void fetchJobs()
    const interval = setInterval(() => {
      void fetchJobs()
    }, 1000)
    return () => {
      clearInterval(interval)
    }
  }, [fetchJobs])

  const cancelJob = async (taskId: string): Promise<void> => {
    try {
      await api.delete<unknown>(`/jobs/${taskId}`)
      void fetchJobs()
    } catch (error) {
      console.error('Failed to cancel job', error)
    }
  }

  return { jobs, cancelJob }
}
