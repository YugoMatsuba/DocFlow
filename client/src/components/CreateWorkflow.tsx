import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreateWorkflowRequest, NodeType, AddNodeRequest } from '../types';
import { workflowApi } from '../api';

const CreateWorkflow: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<CreateWorkflowRequest>({
    name: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Create workflow using backend API
      const newWorkflow = await workflowApi.createWorkflow({
        name: formData.name,
        description: formData.description || undefined
      });

      // Navigate to the created workflow
      navigate(`/workflows/${newWorkflow.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create workflow');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => navigate('/workflows')}
          className="btn btn-secondary btn-sm"
        >
          ← Back
        </button>
        <h1>Create New Workflow</h1>
      </div>

      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name" className="form-label">
                Workflow Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                className="form-control"
                value={formData.name}
                onChange={handleInputChange}
                required
                placeholder="Enter workflow name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description" className="form-label">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                className="form-control"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Enter workflow description"
                rows={3}
              />
            </div>

            {error && (
              <div className="mb-4" style={{ color: 'var(--error-red)' }}>
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !formData.name.trim()}
              >
                {loading && <div className="spinner"></div>}
                Create Workflow
              </button>
              <button
                type="button"
                onClick={() => navigate('/workflows')}
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

export default CreateWorkflow;