import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Job } from '../types';

const API_BASE = 'http://localhost:5000/api';

export const useJobs = () => {
  const [jobs, setJobs] = useState<Job[]>([]);

  const fetchJobs = async () => {
    try {
      const response = await axios.get<Job[]>(`${API_BASE}/jobs`);
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
      await axios.delete<void>(`${API_BASE}/jobs/${taskId}`);
      fetchJobs();
    } catch (error) {
      console.error('Failed to cancel job', error);
    }
  };

  return { jobs, cancelJob };
};
