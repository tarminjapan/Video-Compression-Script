import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:5000/api', // Fallback
});

let isInitialized = false;

export const initializeApi = async () => {
  if (isInitialized) return;

  if (window.electronAPI && window.electronAPI.getApiUrl) {
    try {
      const url = await window.electronAPI.getApiUrl();
      api.defaults.baseURL = url;
    } catch (error) {
      console.error('Failed to get API URL from Electron', error);
    }
  }
  
  isInitialized = true;
};

export const getApiBase = () => api.defaults.baseURL;
