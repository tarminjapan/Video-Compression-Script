export interface BackendStatus {
  running: boolean;
  healthy: boolean;
  port: number;
}

export interface IElectronAPI {
  platform: string;
  getApiUrl: () => Promise<string>;
  getBackendStatus: () => Promise<BackendStatus>;
  restartBackend: () => Promise<boolean>;
}

declare global {
  interface Window {
    electronAPI: IElectronAPI;
  }
}
