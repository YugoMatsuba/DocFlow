export interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  created_at: string;
  updated_at: string;
}

export interface Node {
  id: string;
  name: string;
  node_type: NodeType;
  configuration: Record<string, any>;
  order: number;
  created_at: string;
}

export enum NodeType {
  FORMATTER = 'FORMATTER',
  GENERATIVE_AI = 'GENERATIVE_AI',
  EXTRACT_TEXT = 'EXTRACT_TEXT'
}

export interface Execution {
  id: string;
  workflow_id: string;
  status: ExecutionStatus;
  input_file_path?: string;
  output_data?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export enum ExecutionStatus {
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
}

export interface AddNodeRequest {
  name: string;
  node_type: NodeType;
  configuration: Record<string, any>;
  order?: number;
}