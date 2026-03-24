import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from main import app
from domain.enums.node_type import NodeType
from domain.entities.workflow import Workflow
from domain.entities.node import Node


class TestWorkflowsAPI:
    """Test cases for Workflows API endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)

    @patch("api.dependencies.get_workflow_service")
    @patch("infra.db.database.get_db_session")
    def test_create_workflow_success(self, mock_get_db_session, mock_get_workflow_service):
        """Test successful workflow creation"""
        mock_db_session = AsyncMock()
        mock_get_db_session.return_value = mock_db_session

        mock_service = AsyncMock()
        mock_get_workflow_service.return_value = mock_service

        # Create mock workflow response
        workflow = Workflow.create("Test Workflow", "Test description")
        mock_service.create_workflow.return_value = workflow

        request_data = {
            "name": "Test Workflow",
            "description": "Test description"
        }

        response = self.client.post("/api/workflows/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["description"] == "Test description"
        assert "id" in data
        assert data["is_active"] == True
        assert data["nodes"] == []

        mock_service.create_workflow.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch("api.dependencies.get_workflow_service")
    def test_create_workflow_server_error(self, mock_get_workflow_service):
        """Test workflow creation with server error"""
        mock_service = AsyncMock()
        mock_service.create_workflow.side_effect = Exception("Database error")
        mock_get_workflow_service.return_value = mock_service

        request_data = {
            "name": "Test Workflow"
        }

        response = self.client.post("/api/workflows/", json=request_data)

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to create workflow"

    @patch("api.dependencies.get_workflow_service")
    def test_list_workflows_success(self, mock_get_workflow_service):
        """Test successful workflow listing"""
        mock_service = AsyncMock()
        mock_get_workflow_service.return_value = mock_service

        # Create mock workflows
        workflow1 = Workflow.create("Workflow 1")
        workflow2 = Workflow.create("Workflow 2")
        mock_service.list_workflows.return_value = [workflow1, workflow2]

        response = self.client.get("/api/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Workflow 1"
        assert data[1]["name"] == "Workflow 2"

        mock_service.list_workflows.assert_called_once()

    @patch("api.dependencies.get_workflow_service")
    def test_list_workflows_server_error(self, mock_get_workflow_service):
        """Test workflow listing with server error"""
        mock_service = AsyncMock()
        mock_service.list_workflows.side_effect = Exception("Database error")
        mock_get_workflow_service.return_value = mock_service

        response = self.client.get("/api/workflows/")

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to list workflows"

    @patch("api.dependencies.get_workflow_service")
    def test_get_workflow_success(self, mock_get_workflow_service):
        """Test successful workflow retrieval"""
        mock_service = AsyncMock()
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        workflow = Workflow.create("Test Workflow")
        workflow.id = workflow_id

        # Add a node to the workflow
        node = Node.create(
            name="Test Node",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow_id,
            order=0
        )
        workflow.nodes.append(node)

        mock_service.get_workflow.return_value = workflow

        response = self.client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == "Test Workflow"
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["name"] == "Test Node"
        assert data["nodes"][0]["node_type"] == "EXTRACT_TEXT"

        mock_service.get_workflow.assert_called_once_with(workflow_id)

    @patch("api.dependencies.get_workflow_service")
    def test_get_workflow_not_found(self, mock_get_workflow_service):
        """Test getting non-existent workflow"""
        mock_service = AsyncMock()
        mock_service.get_workflow.return_value = None
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "nonexistent-workflow"
        response = self.client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Workflow not found"

    @patch("api.dependencies.get_workflow_service")
    @patch("infra.db.database.get_db_session")
    def test_add_node_success(self, mock_get_db_session, mock_get_workflow_service):
        """Test successful node addition"""
        mock_db_session = AsyncMock()
        mock_get_db_session.return_value = mock_db_session

        mock_service = AsyncMock()
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        node = Node.create(
            name="Test Node",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow_id,
            order=0
        )

        mock_service.add_node.return_value = node

        request_data = {
            "name": "Test Node",
            "node_type": "FORMATTER",
            "configuration": {"format_type": "uppercase"},
            "order": 0
        }

        response = self.client.post(f"/api/workflows/{workflow_id}/nodes", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Node"
        assert data["node_type"] == "FORMATTER"
        assert data["configuration"]["format_type"] == "uppercase"
        assert data["order"] == 0

        mock_service.add_node.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch("api.dependencies.get_workflow_service")
    def test_add_node_workflow_not_found(self, mock_get_workflow_service):
        """Test adding node to non-existent workflow"""
        mock_service = AsyncMock()
        mock_service.add_node.return_value = None
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "nonexistent-workflow"
        request_data = {
            "name": "Test Node",
            "node_type": "FORMATTER",
            "configuration": {"format_type": "uppercase"}
        }

        response = self.client.post(f"/api/workflows/{workflow_id}/nodes", json=request_data)

        assert response.status_code == 404
        assert response.json()["detail"] == "Workflow not found"

    @patch("api.dependencies.get_workflow_service")
    def test_add_node_invalid_configuration(self, mock_get_workflow_service):
        """Test adding node with invalid configuration"""
        mock_service = AsyncMock()
        mock_service.add_node.side_effect = ValueError("Invalid node configuration")
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        request_data = {
            "name": "Test Node",
            "node_type": "FORMATTER",
            "configuration": {"invalid_key": "value"}
        }

        response = self.client.post(f"/api/workflows/{workflow_id}/nodes", json=request_data)

        assert response.status_code == 400
        assert "Invalid node configuration" in response.json()["detail"]

    @patch("api.dependencies.get_workflow_service")
    def test_add_node_server_error(self, mock_get_workflow_service):
        """Test adding node with server error"""
        mock_service = AsyncMock()
        mock_service.add_node.side_effect = Exception("Database error")
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        request_data = {
            "name": "Test Node",
            "node_type": "FORMATTER",
            "configuration": {"format_type": "uppercase"}
        }

        response = self.client.post(f"/api/workflows/{workflow_id}/nodes", json=request_data)

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to add node"

    @patch("api.dependencies.get_workflow_service")
    def test_validate_workflow_valid(self, mock_get_workflow_service):
        """Test validation of valid workflow"""
        mock_service = AsyncMock()
        mock_service.validate_workflow.return_value = []  # No errors
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        response = self.client.get(f"/api/workflows/{workflow_id}/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["errors"] == []

        mock_service.validate_workflow.assert_called_once_with(workflow_id)

    @patch("api.dependencies.get_workflow_service")
    def test_validate_workflow_invalid(self, mock_get_workflow_service):
        """Test validation of invalid workflow"""
        mock_service = AsyncMock()
        mock_service.validate_workflow.return_value = ["Workflow must have at least one node"]
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "test-workflow-id"
        response = self.client.get(f"/api/workflows/{workflow_id}/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert len(data["errors"]) == 1
        assert "must have at least one node" in data["errors"][0]

    @patch("api.dependencies.get_workflow_service")
    def test_validate_workflow_not_found(self, mock_get_workflow_service):
        """Test validation of non-existent workflow"""
        mock_service = AsyncMock()
        mock_service.validate_workflow.return_value = ["Workflow not found"]
        mock_get_workflow_service.return_value = mock_service

        workflow_id = "nonexistent-workflow"
        response = self.client.get(f"/api/workflows/{workflow_id}/validate")

        assert response.status_code == 404
        assert response.json()["detail"] == "Workflow not found"

    def test_create_workflow_invalid_request_body(self):
        """Test creating workflow with invalid request body"""
        # Missing required name field
        request_data = {
            "description": "Test description"
        }

        response = self.client.post("/api/workflows/", json=request_data)

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_add_node_invalid_node_type(self):
        """Test adding node with invalid node type"""
        workflow_id = "test-workflow-id"
        request_data = {
            "name": "Test Node",
            "node_type": "INVALID_TYPE",
            "configuration": {}
        }

        response = self.client.post(f"/api/workflows/{workflow_id}/nodes", json=request_data)

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()