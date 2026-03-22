import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Execution, ExecutionStatus } from '../types';
import { listExecutions } from '../api';

const ExecutionList: React.FC = () => {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(false);
  const [batchMessage, setBatchMessage] = useState<string | null>(null);
  const location = useLocation();
  const optimisticExecutionsRef = useRef<Execution[]>([]);

  useEffect(() => {
    const state = location.state as { newExecution?: Execution; newExecutions?: Execution[]; batchMessage?: string | null } | null;
    if (state?.newExecutions?.length) {
      optimisticExecutionsRef.current = state.newExecutions;
      setBatchMessage(state.batchMessage ?? null);
      window.history.replaceState(null, '');
    } else if (state?.newExecution) {
      optimisticExecutionsRef.current = [state.newExecution];
      setBatchMessage(state.batchMessage ?? null);
      window.history.replaceState(null, '');
    }

    loadExecutions();
  }, []);

  const loadExecutions = async () => {
    try {
      setLoading(true);
      const executionsData = await listExecutions(50, 0); // Get more results

      let mergedExecutions = executionsData;
      const optimisticExecutions = optimisticExecutionsRef.current;

      if (optimisticExecutions.length > 0) {
        const executionMap = new Map(
          executionsData.map((execution) => [execution.id, execution])
        );

        for (const optimisticExecution of optimisticExecutions) {
          if (!executionMap.has(optimisticExecution.id)) {
            executionMap.set(optimisticExecution.id, optimisticExecution);
          }
        }

        mergedExecutions = Array.from(executionMap.values()).sort(
          (left, right) =>
            new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
        );
      }

      setExecutions(mergedExecutions);
    } catch (error) {
      console.error('Failed to load executions:', error);
      if (optimisticExecutionsRef.current.length > 0) {
        setExecutions(optimisticExecutionsRef.current);
      } else {
        setExecutions([]);
      }
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner"></div>
        <p className="mt-2">Loading executions...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1>Workflow Executions</h1>
        <Link to="/executions/create" className="btn btn-primary">
          Start New Execution
        </Link>
      </div>

      {batchMessage && (
        <div className="card mb-4">
          <div className="card-body" style={{ color: 'var(--warning-orange)' }}>
            {batchMessage}
          </div>
        </div>
      )}

      {executions.length === 0 ? (
        <div className="card">
          <div className="card-body text-center">
            <p>No executions found</p>
            <Link to="/executions/create" className="btn btn-primary mt-2">
              Start First Execution
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {executions.map((execution) => (
            <div key={execution.id} className="card">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div style={{ flex: 1 }}>
                    <div className="flex items-center gap-2 mb-2">
                      <span style={{ fontSize: '1.2rem' }}>
                        {getStatusIcon(execution.status)}
                      </span>
                      <h3>Execution #{execution.id.slice(-8)}</h3>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: getStatusColor(execution.status),
                          color: 'white'
                        }}
                      >
                        {execution.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          Workflow ID: {execution.workflow_id}
                        </p>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          Started: {new Date(execution.created_at).toLocaleString()}
                        </p>
                        {execution.completed_at && (
                          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            Completed: {new Date(execution.completed_at).toLocaleString()}
                          </p>
                        )}
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          Duration: {formatDuration(execution.created_at, execution.completed_at)}
                        </p>
                      </div>

                      <div>
                        {execution.input_file_path && (
                          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            Input File: {execution.input_file_path.split('/').pop()}
                          </p>
                        )}

                        {execution.error_message && (
                          <p className="text-sm mt-2" style={{ color: 'var(--error-red)' }}>
                            Error: {execution.error_message}
                          </p>
                        )}

                        {execution.output_data && execution.status === ExecutionStatus.COMPLETED && (
                          <p className="text-sm mt-2" style={{ color: 'var(--success-green)' }}>
                            ✓ Processing completed successfully
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Link
                      to={`/executions/${execution.id}`}
                      className="btn btn-primary btn-sm"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExecutionList;
