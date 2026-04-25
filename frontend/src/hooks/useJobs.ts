import { useState, useEffect } from 'react';
import { api, initializeApi } from '../services/api';
import type { Job } from '../types';

export const useJobs = () => {
  const [jobs, setJobs] = useState<Job[]>([]);

  const fetchJobs = async () => {
    try {
      await initializeApi();
      const response = await api.get<Job[]>('/jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs', error);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 1000);
    return () => clearInterval(interval);
  }, []);

  const cancelJob = async (taskId: string) => {
    try {
      await api.delete<void>(`/jobs/${taskId}`);
      fetchJobs();
    } catch (error) {
      console.error('Failed to cancel job', error);
    }
  };

  return { jobs, cancelJob };
};
