import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Workflow } from '../types';
import { workflowApi } from '../api';

interface WorkflowListProps {
  onSelectWorkflow?: (workflow: Workflow) => void;
}

const WorkflowList: React.FC<WorkflowListProps> = ({ onSelectWorkflow }) => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiWorkflows = await workflowApi.getWorkflows();
      setWorkflows(apiWorkflows);
    } catch (err: any) {
      setError(err.message || 'Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWorkflow = (workflow: Workflow) => {
    if (onSelectWorkflow) {
      onSelectWorkflow(workflow);
    }
  };


  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner"></div>
        <p className="mt-2">Loading workflows...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body text-center">
          <p style={{ color: 'var(--error-red)' }}>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2>Workflows</h2>
        <Link to="/workflows/create" className="btn btn-primary">
          Create Workflow
        </Link>
      </div>

      {workflows.length === 0 ? (
        <div className="card">
          <div className="card-body text-center">
            <p>No workflows found</p>
            <Link to="/workflows/create" className="btn btn-primary mt-2">
              Create Your First Workflow
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="card">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div>
                    <h3>{workflow.name}</h3>
                    {workflow.description && (
                      <p className="mt-1">{workflow.description}</p>
                    )}
                    <div className="mt-2">
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {workflow.nodes?.length || 0} nodes
                      </span>
                      <span className="ml-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                        Created: {new Date(workflow.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {onSelectWorkflow && (
                      <button
                        onClick={() => handleSelectWorkflow(workflow)}
                        className="btn btn-secondary btn-sm"
                      >
                        Select
                      </button>
                    )}
                    <Link
                      to={`/workflows/${workflow.id}`}
                      className="btn btn-primary btn-sm"
                    >
                      View
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

export default WorkflowList;