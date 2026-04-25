export type JobStatus = 'starting' | 'running' | 'success' | 'failed';
export type JobType = 'video' | 'audio';

export interface Progress {
  percent: number;
  eta: number;
  speed?: number;
}

export interface TaskResult {
  compression_ratio?: number;
  [key: string]: any;
}

export interface Job {
  id: string;
  status: JobStatus;
  progress: Progress | null;
  result: TaskResult | null;
  type: JobType;
}

export interface MediaInfo {
  type: 'video' | 'audio';
  duration: number;
  width?: number;
  height?: number;
  bitrate?: number;
}
