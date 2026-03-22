import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import WorkflowList from './components/WorkflowList';
import CreateWorkflow from './components/CreateWorkflow';
import WorkflowDetail from './components/WorkflowDetail';
import ExecutionList from './components/ExecutionList';
import CreateExecution from './components/CreateExecution';
import ExecutionDetail from './components/ExecutionDetail';
import './styles/globals.css';

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/workflows" replace />} />
          <Route path="/workflows" element={<WorkflowList />} />
          <Route path="/workflows/create" element={<CreateWorkflow />} />
          <Route path="/workflows/:id" element={<WorkflowDetail />} />
          <Route path="/executions" element={<ExecutionList />} />
          <Route path="/executions/create" element={<CreateExecution />} />
          <Route path="/executions/:id" element={<ExecutionDetail />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;