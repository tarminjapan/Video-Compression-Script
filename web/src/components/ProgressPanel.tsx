import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

interface Job {
  id: string;
  status: string;
  progress: any;
  result: any;
  type: string;
}

interface ProgressPanelProps {
  jobs: Job[];
  onCancel: (id: string) => void;
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({ jobs, onCancel }) => {
  const { t } = useTranslation();

  if (jobs.length === 0) return null;

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
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${job.progress.percent}%` }}
                  ></div>
                </div>
                <div className="job-stats">
                  <span>{Math.round(job.progress.percent)}%</span>
                  <span>ETA: {Math.round(job.progress.eta)}s</span>
                  <span>Speed: {job.progress.speed?.toFixed(1)}x</span>
                </div>
              </div>
            )}

            {job.status === 'success' && job.result && (
              <div className="job-result">
                <span>-{job.result.compression_ratio?.toFixed(1)}%</span>
              </div>
            )}

            {(job.status === 'running' || job.status === 'starting') && (
              <button className="cancel-button" onClick={() => onCancel(job.id)}>
                <X size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressPanel;
