import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Execution, ExecutionStatus } from '../types';
import { getExecution } from '../api';

const ExecutionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadExecution(id);
      // Load execution data once on mount
    }
  }, [id]);

  const loadExecution = async (executionId: string) => {
    try {
      const executionData = await getExecution(executionId);
      setExecution(executionData);
    } catch (error) {
      console.error('Failed to load execution:', error);
      setExecution(null);
    }
  };

  const getStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING: return 'var(--accent-blue-500)';
      case ExecutionStatus.COMPLETED: return 'var(--success-green)';
      case ExecutionStatus.FAILED: return 'var(--error-red)';
      default: return 'var(--primary-blue-500)';
    }
  };

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING: return '🔄';
      case ExecutionStatus.COMPLETED: return '✅';
      case ExecutionStatus.FAILED: return '❌';
      default: return '⏳';
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);

    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const renderJsonData = (data: any, title: string) => {
    if (!data) return null;

    return (
      <div className="form-group">
        <label className="form-label">{title}</label>
        <pre style={{
          backgroundColor: 'var(--primary-blue-700)',
          padding: '1rem',
          borderRadius: '0.375rem',
          fontSize: '0.875rem',
          overflow: 'auto',
          maxHeight: '400px',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-color)'
        }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  };

  if (!execution) {
    return (
      <div className="card">
        <div className="card-body text-center">
          <p>Execution not found</p>
          <button onClick={() => navigate('/executions')} className="btn btn-primary mt-2">
            Back to Executions
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => navigate('/executions')}
          className="btn btn-secondary btn-sm"
        >
          ← Back
        </button>
        <h1>Execution Details</h1>
      </div>

      {/* Execution Status Card */}
      <div className="card mb-4">
        <div className="card-header">
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '1.5rem' }}>
              {getStatusIcon(execution.status)}
            </span>
            <h2>Execution #{execution.id.slice(-8)}</h2>
            <span
              className="badge"
              style={{
                backgroundColor: getStatusColor(execution.status),
                color: 'white',
                fontSize: '0.875rem'
              }}
            >
              {execution.status}
            </span>
          </div>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4>Execution Info</h4>
              <div className="mt-2 space-y-1">
                <p className="text-sm">
                  <strong>Execution ID:</strong> {execution.id}
                </p>
                <p className="text-sm">
                  <strong>Workflow ID:</strong> {execution.workflow_id}
                </p>
                <p className="text-sm">
                  <strong>Started:</strong> {new Date(execution.created_at).toLocaleString()}
                </p>
                <p className="text-sm">
                  <strong>Last Updated:</strong> {new Date(execution.updated_at).toLocaleString()}
                </p>
                {execution.completed_at && (
                  <p className="text-sm">
                    <strong>Completed:</strong> {new Date(execution.completed_at).toLocaleString()}
                  </p>
                )}
                <p className="text-sm">
                  <strong>Duration:</strong> {formatDuration(execution.created_at, execution.completed_at)}
                </p>
                {execution.input_file_path && (
                  <p className="text-sm">
                    <strong>Input File:</strong> {execution.input_file_path.split('/').pop()}
                  </p>
                )}
              </div>
            </div>

            <div>
              <h4>Status</h4>
              <div className="mt-2">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm">Status: {execution.status}</span>
                  {execution.status === ExecutionStatus.RUNNING && (
                    <div className="spinner" style={{ width: '1rem', height: '1rem' }}></div>
                  )}
                </div>
              </div>

              {execution.error_message && (
                <div className="mt-4">
                  <h4 style={{ color: 'var(--error-red)' }}>Error Message</h4>
                  <div
                    className="mt-2 p-3"
                    style={{
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid var(--error-red)',
                      borderRadius: '0.375rem',
                      color: 'var(--error-red)',
                      fontSize: '0.875rem'
                    }}
                  >
                    {execution.error_message}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Output Data */}
      <div className="grid grid-cols-1 gap-4">
        {/* Output Data */}
        {execution.output_data && (
          <div className="card">
            <div className="card-header">
              <h3>Workflow Output</h3>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Processed Result</label>
                <div
                  style={{
                    backgroundColor: 'var(--primary-blue-800)',
                    border: '2px solid var(--accent-blue-500)',
                    borderRadius: '0.5rem',
                    padding: '1rem',
                    marginTop: '0.5rem'
                  }}
                >
                  <pre style={{
                    color: 'var(--text-primary)',
                    fontSize: '0.875rem',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    margin: 0
                  }}>
                    {execution.output_data}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Show placeholder if no output yet */}
        {!execution.output_data && execution.status !== ExecutionStatus.FAILED && (
          <div className="card">
            <div className="card-header">
              <h3>Workflow Output</h3>
            </div>
            <div className="card-body text-center">
              <p style={{ color: 'var(--text-muted)' }}>
                {execution.status === ExecutionStatus.RUNNING
                  ? 'Processing workflow... Output will appear here when complete.'
                  : 'No output data available yet.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionDetail;
