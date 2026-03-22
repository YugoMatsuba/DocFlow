import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Workflow } from '../types';
import WorkflowList from './WorkflowList';
import { startExecution } from '../api';

const CreateExecution: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWorkflowSelector, setShowWorkflowSelector] = useState(true);

  useEffect(() => {
    const workflowId = searchParams.get('workflow_id');
    if (workflowId) {
      // Load specific workflow from API
      loadWorkflow(workflowId);
    }
  }, [searchParams]);

  const loadWorkflow = async (workflowId: string) => {
    try {
      const { workflowApi } = await import('../api');
      const workflow = await workflowApi.getWorkflow(workflowId);
      setSelectedWorkflow(workflow);
      setShowWorkflowSelector(false);
    } catch (error) {
      console.error('Failed to load workflow:', error);
      setError('Failed to load the specified workflow');
    }
  };

  const handleWorkflowSelect = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setShowWorkflowSelector(false);
  };

  const getFileKey = (file: File) => `${file.name}-${file.size}-${file.lastModified}`;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) {
      return;
    }

    const invalidFiles = files.filter((file) => file.type !== 'application/pdf');
    const validFiles = files.filter((file) => file.type === 'application/pdf');

    if (validFiles.length > 0) {
      setSelectedFiles((prevFiles) => {
        const mergedFiles = [...prevFiles];
        const existingKeys = new Set(prevFiles.map(getFileKey));

        for (const file of validFiles) {
          const fileKey = getFileKey(file);
          if (!existingKeys.has(fileKey)) {
            mergedFiles.push(file);
            existingKeys.add(fileKey);
          }
        }

        return mergedFiles;
      });
    }

    if (invalidFiles.length > 0) {
      setError(`Only PDF files are supported: ${invalidFiles.map((file) => file.name).join(', ')}`);
    } else {
      setError(null);
    }

    // Allow selecting the same file again in a later picker interaction.
    e.target.value = '';
  };

  const handleStartExecution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkflow || selectedFiles.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled(
        selectedFiles.map((file) => startExecution(selectedWorkflow.id, file))
      );

      const startedExecutions = results
        .filter((result): result is PromiseFulfilledResult<any> => result.status === 'fulfilled')
        .map((result) => result.value);
      const failedCount = results.length - startedExecutions.length;

      if (startedExecutions.length === 0) {
        setError('Failed to start executions for all selected files');
        return;
      }

      navigate('/executions', {
        state: {
          newExecutions: startedExecutions,
          batchMessage:
            failedCount > 0
              ? `${startedExecutions.length} execution(s) started. ${failedCount} file(s) failed to start.`
              : null,
        },
      });
    } catch (err: any) {
      setError(err.message || 'Failed to start execution');
    } finally {
      setLoading(false);
    }
  };

  if (showWorkflowSelector) {
    return (
      <div>
        <div className="mb-4">
          <h1>Start New Execution</h1>
          <p>Select a workflow to execute:</p>
        </div>
        <WorkflowList onSelectWorkflow={handleWorkflowSelect} />
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
        <h1>Start Execution</h1>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h2>Selected Workflow</h2>
            <button
              onClick={() => setShowWorkflowSelector(true)}
              className="btn btn-secondary btn-sm"
            >
              Change Workflow
            </button>
          </div>
        </div>
        <div className="card-body">
          <h3>{selectedWorkflow?.name}</h3>
          {selectedWorkflow?.description && (
            <p className="mt-1">{selectedWorkflow.description}</p>
          )}
          <div className="mt-2">
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {selectedWorkflow?.nodes?.length || 0} nodes
            </span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>PDF File Upload</h3>
        </div>
        <div className="card-body">
          <form onSubmit={handleStartExecution}>
            <div className="form-group">
              <label htmlFor="pdfFile" className="form-label">
                Select PDF File(s)
              </label>
              <input
                id="pdfFile"
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileSelect}
                className="form-control"
              />
              <small style={{ color: 'var(--text-muted)' }}>
                Upload one or more PDF files to process through the selected workflow. Each PDF will start a separate execution.
              </small>
            </div>

            {selectedFiles.length > 0 && (
              <div className="mt-4 p-3" style={{ backgroundColor: 'var(--surface-secondary)', borderRadius: '8px' }}>
                <h4 className="text-sm font-medium mb-2">
                  Selected Files ({selectedFiles.length})
                </h4>
                <div className="grid grid-cols-1 gap-2">
                  {selectedFiles.map((file) => (
                    <div key={`${file.name}-${file.size}-${file.lastModified}`} className="flex items-center gap-2">
                      <span className="text-sm">{file.name}</span>
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4" style={{ color: 'var(--error-red)' }}>
                {error}
              </div>
            )}

            <div className="flex gap-2 mt-6">
              <button
                type="submit"
                className="btn btn-success"
                disabled={loading || !selectedWorkflow || selectedFiles.length === 0}
              >
                {loading && <div className="spinner"></div>}
                Start Processing {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}
              </button>
              <button
                type="button"
                onClick={() => navigate('/executions')}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateExecution;
