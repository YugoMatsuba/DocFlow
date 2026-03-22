import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Workflow, Node, NodeType, AddNodeRequest } from '../types';
import { workflowApi } from '../api';

const WorkflowDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [showAddNode, setShowAddNode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nodeForm, setNodeForm] = useState<AddNodeRequest>({
    name: '',
    node_type: NodeType.FORMATTER,
    configuration: {}
  });

  const [configText, setConfigText] = useState<string>('{}');

  useEffect(() => {
    if (id) {
      loadWorkflow(id);
    }
  }, [id]);

  const loadWorkflow = async (workflowId: string) => {
    try {
      const workflow = await workflowApi.getWorkflow(workflowId);
      setWorkflow(workflow);
    } catch (apiError) {
      console.error('Failed to load workflow:', apiError);
      setWorkflow(null);
    }
  };

  const handleAddNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflow) return;

    try {
      setLoading(true);
      setError(null);

      const newNode = await workflowApi.addNode(workflow.id, {
        name: nodeForm.name,
        node_type: nodeForm.node_type,
        configuration: nodeForm.configuration,
        order: workflow.nodes?.length || 0
      });

      setWorkflow((prev) => {
        if (!prev) {
          return prev;
        }

        const nextNodes = [...(prev.nodes ?? []), newNode].sort(
          (left, right) => left.order - right.order
        );

        return {
          ...prev,
          nodes: nextNodes,
        };
      });

      // Reset form on success
      setShowAddNode(false);
      setNodeForm({
        name: '',
        node_type: NodeType.FORMATTER,
        configuration: {}
      });
      setConfigText('{}');
    } catch (err: any) {
      setError(err.message || 'Failed to add node');
    } finally {
      setLoading(false);
    }
  };

  const handleStartExecution = () => {
    if (workflow) {
      navigate(`/executions/create?workflow_id=${workflow.id}`);
    }
  };


  const getNodeTypeColor = (nodeType: NodeType) => {
    switch (nodeType) {
      case NodeType.EXTRACT_TEXT: return 'var(--warning-orange)';
      case NodeType.GENERATIVE_AI: return 'var(--accent-blue-500)';
      case NodeType.FORMATTER: return 'var(--success-green)';
      default: return 'var(--primary-blue-500)';
    }
  };

  const renderNodeConfiguration = (config: any) => {
    return (
      <pre style={{
        backgroundColor: 'var(--primary-blue-700)',
        padding: '0.5rem',
        borderRadius: '0.25rem',
        fontSize: '0.75rem',
        overflow: 'auto',
        color: 'var(--text-secondary)'
      }}>
        {JSON.stringify(config, null, 2)}
      </pre>
    );
  };

  if (!workflow) {
    return (
      <div className="card">
        <div className="card-body text-center">
          <p>Workflow not found</p>
          <button onClick={() => navigate('/workflows')} className="btn btn-primary mt-2">
            Back to Workflows
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => navigate('/workflows')}
          className="btn btn-secondary btn-sm"
        >
          ← Back
        </button>
        <h1>{workflow.name}</h1>
      </div>

      {error && (
        <div className="mb-4 card">
          <div className="card-body" style={{ color: 'var(--error-red)' }}>
            {error}
          </div>
        </div>
      )}

      {/* Workflow Info */}
      <div className="card mb-4">
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div>
              <h2>{workflow.name}</h2>
              {workflow.description && <p className="mt-2">{workflow.description}</p>}
              <div className="mt-2">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Created: {new Date(workflow.created_at).toLocaleString()}
                </span>
                {workflow.updated_at !== workflow.created_at && (
                  <span className="ml-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                    Updated: {new Date(workflow.updated_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddNode(true)}
                className="btn btn-secondary"
              >
                Add Node
              </button>
              <button
                onClick={handleStartExecution}
                className="btn btn-success"
                disabled={!workflow.nodes || workflow.nodes.length === 0}
              >
                Run Workflow
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Add Node Form */}
      {showAddNode && (
        <div className="card mb-4">
          <div className="card-header">
            <h3>Add New Node</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleAddNode}>
              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label className="form-label">Node Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={nodeForm.name}
                    onChange={(e) => setNodeForm(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Node Type *</label>
                  <select
                    className="form-control"
                    value={nodeForm.node_type}
                    onChange={(e) => setNodeForm(prev => ({ ...prev, node_type: e.target.value as NodeType }))}
                  >
                    <option value={NodeType.FORMATTER}>Formatter</option>
                    <option value={NodeType.GENERATIVE_AI}>Generative AI</option>
                    <option value={NodeType.EXTRACT_TEXT}>Extract Text</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Configuration (JSON)</label>
                <textarea
                  className="form-control"
                  rows={6}
                  value={configText}
                  onChange={(e) => {
                    setConfigText(e.target.value);
                    try {
                      const config = JSON.parse(e.target.value);
                      setNodeForm(prev => ({ ...prev, configuration: config }));
                      setError(null);
                    } catch (err) {
                      setError('Invalid JSON format in configuration');
                    }
                  }}
                  placeholder={`{\n  "prompt": "Your AI prompt here",\n  "model": "gpt-3.5-turbo",\n  "temperature": 0.7\n}`}
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    backgroundColor: 'var(--surface-secondary)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)'
                  }}
                />
                <small style={{ color: 'var(--text-muted)' }}>
                  Enter valid JSON configuration for the node
                </small>
              </div>
              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading && <div className="spinner"></div>}
                  Add Node
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddNode(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Nodes List */}
      <div className="card">
        <div className="card-header">
          <h3>Workflow Nodes ({workflow.nodes?.length || 0})</h3>
        </div>
        <div className="card-body">
          {!workflow.nodes || workflow.nodes.length === 0 ? (
            <div className="text-center">
              <p>No nodes in this workflow</p>
              <button
                onClick={() => setShowAddNode(true)}
                className="btn btn-primary mt-2"
              >
                Add First Node
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {workflow.nodes.map((node, index) => (
                <div
                  key={node.id}
                  className="card"
                  style={{ borderLeft: `4px solid ${getNodeTypeColor(node.node_type)}` }}
                >
                  <div className="card-body">
                    <div className="flex justify-between items-start">
                      <div style={{ flex: 1 }}>
                        <div className="flex items-center gap-2">
                          <span
                            style={{
                              backgroundColor: 'var(--primary-blue-700)',
                              color: 'var(--text-primary)',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '0.25rem',
                              fontSize: '0.75rem',
                              fontWeight: '600'
                            }}
                          >
                            {index + 1}
                          </span>
                          <h4>{node.name}</h4>
                          <span
                            className="badge"
                            style={{ backgroundColor: getNodeTypeColor(node.node_type), color: 'white' }}
                          >
                            {node.node_type}
                          </span>
                        </div>
                        <div className="mt-2">
                          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            Configuration:
                          </p>
                          {renderNodeConfiguration(node.configuration)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowDetail;
