import axios from 'axios';
import {
  Workflow,
  Execution,
  CreateWorkflowRequest,
  AddNodeRequest
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const workflowApi = {
  // Workflow operations
  createWorkflow: async (data: CreateWorkflowRequest): Promise<Workflow> => {
    const response = await apiClient.post('/workflows/', data);
    return response.data;
  },

  getWorkflows: async (): Promise<Workflow[]> => {
    const response = await apiClient.get('/workflows/');
    return response.data;
  },

  getWorkflow: async (workflowId: string): Promise<Workflow> => {
    const response = await apiClient.get(`/workflows/${workflowId}`);
    return response.data;
  },

  addNode: async (workflowId: string, data: AddNodeRequest): Promise<any> => {
    const response = await apiClient.post(`/workflows/${workflowId}/nodes`, data);
    return response.data;
  },

  validateWorkflow: async (workflowId: string): Promise<{valid: boolean; errors: string[]}> => {
    const response = await apiClient.get(`/workflows/${workflowId}/validate`);
    return response.data;
  },


  // Execution operations
  startExecution: async (workflowId: string, file: File): Promise<Execution> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(
      `${API_BASE_URL}/executions/?workflow_id=${workflowId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // Longer timeout for file uploads
      }
    );
    return response.data;
  },

  getExecution: async (executionId: string): Promise<Execution> => {
    const response = await apiClient.get(`/executions/${executionId}`);
    return response.data;
  },

  listExecutions: async (limit: number = 20, offset: number = 0): Promise<Execution[]> => {
    const response = await apiClient.get(`/executions/?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{status: string}> => {
    const response = await apiClient.get('/health');
    return response.data;
  }
};

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 404) {
      console.error('Resource not found:', error.response.data);
    } else if (error.response?.status >= 500) {
      console.error('Server error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Export commonly used functions for easy importing
export const { startExecution, getExecution, listExecutions } = workflowApi;