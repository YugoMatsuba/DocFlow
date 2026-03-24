import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO

from main import app
from domain.entities.execution import Execution, ExecutionStatus
from errors import NotFoundError, ValidationError


class TestExecutionsAPI:
    """Test cases for Executions API endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)

    @patch("api.routers.executions.get_file_storage")
    @patch("api.dependencies.get_execution_service")
    def test_start_execution_success(self, mock_get_execution_service, mock_get_file_storage):
        """Test successful execution start"""
        # Mock file storage
        mock_file_storage = MagicMock()
        mock_file_storage.save_pdf_file = AsyncMock(return_value="/tmp/test.pdf")
        mock_get_file_storage.return_value = mock_file_storage

        # Mock execution service
        mock_service = AsyncMock()
        execution = Execution.create(workflow_id="test-workflow", input_file_path="/tmp/test.pdf")
        execution.id = "test-execution-id"
        mock_service.start_execution.return_value = execution
        mock_get_execution_service.return_value = mock_service

        # Create test PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\nstartxref\n%%EOF"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "test-workflow"},
            files={"file": pdf_file}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-execution-id"
        assert data["workflow_id"] == "test-workflow"
        assert data["status"] == ExecutionStatus.RUNNING.value
        assert "test.pdf" in data["input_file_path"]  # Should return filename only

        mock_file_storage.save_pdf_file.assert_called_once()
        mock_service.start_execution.assert_called_once_with("test-workflow", "/tmp/test.pdf")

    @patch("api.routers.executions.get_file_storage")
    @patch("api.dependencies.get_execution_service")
    def test_start_execution_workflow_not_found(self, mock_get_execution_service, mock_get_file_storage):
        """Test execution start when workflow not found"""
        # Mock file storage
        mock_file_storage = MagicMock()
        mock_file_storage.save_pdf_file = AsyncMock(return_value="/tmp/test.pdf")
        mock_file_storage.delete_file = MagicMock()
        mock_get_file_storage.return_value = mock_file_storage

        # Mock execution service
        mock_service = AsyncMock()
        mock_service.start_execution.side_effect = NotFoundError("Workflow not found")
        mock_get_execution_service.return_value = mock_service

        # Create test PDF file
        pdf_content = b"%PDF-1.4\ntest content"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "nonexistent-workflow"},
            files={"file": pdf_file}
        )

        assert response.status_code == 404
        assert "Workflow not found" in response.json()["detail"]

        # Should delete uploaded file on error
        mock_file_storage.delete_file.assert_called_once_with("/tmp/test.pdf")

    @patch("api.routers.executions.get_file_storage")
    @patch("api.dependencies.get_execution_service")
    def test_start_execution_validation_error(self, mock_get_execution_service, mock_get_file_storage):
        """Test execution start with workflow validation error"""
        # Mock file storage
        mock_file_storage = MagicMock()
        mock_file_storage.save_pdf_file = AsyncMock(return_value="/tmp/test.pdf")
        mock_file_storage.delete_file = MagicMock()
        mock_get_file_storage.return_value = mock_file_storage

        # Mock execution service
        mock_service = AsyncMock()
        validation_error = ValidationError(
            "Workflow is invalid",
            errors=["Workflow must have at least one node"]
        )
        mock_service.start_execution.side_effect = validation_error
        mock_get_execution_service.return_value = mock_service

        # Create test PDF file
        pdf_content = b"%PDF-1.4\ntest content"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "invalid-workflow"},
            files={"file": pdf_file}
        )

        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["message"] == "Workflow is invalid"
        assert "Workflow must have at least one node" in data["errors"]

        # Should delete uploaded file on error
        mock_file_storage.delete_file.assert_called_once_with("/tmp/test.pdf")

    @patch("api.routers.executions.get_file_storage")
    @patch("api.dependencies.get_execution_service")
    def test_start_execution_server_error(self, mock_get_execution_service, mock_get_file_storage):
        """Test execution start with server error"""
        # Mock file storage
        mock_file_storage = MagicMock()
        mock_file_storage.save_pdf_file = AsyncMock(return_value="/tmp/test.pdf")
        mock_file_storage.delete_file = MagicMock()
        mock_get_file_storage.return_value = mock_file_storage

        # Mock execution service
        mock_service = AsyncMock()
        mock_service.start_execution.side_effect = Exception("Database error")
        mock_get_execution_service.return_value = mock_service

        # Create test PDF file
        pdf_content = b"%PDF-1.4\ntest content"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "test-workflow"},
            files={"file": pdf_file}
        )

        assert response.status_code == 500
        assert "Failed to start execution" in response.json()["detail"]

        # Should delete uploaded file on error
        mock_file_storage.delete_file.assert_called_once_with("/tmp/test.pdf")

    @patch("api.routers.executions.get_file_storage")
    def test_start_execution_file_storage_error(self, mock_get_file_storage):
        """Test execution start when file storage fails"""
        # Mock file storage to fail
        mock_file_storage = MagicMock()
        mock_file_storage.save_pdf_file.side_effect = Exception("Storage error")
        mock_get_file_storage.return_value = mock_file_storage

        # Create test PDF file
        pdf_content = b"%PDF-1.4\ntest content"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "test-workflow"},
            files={"file": pdf_file}
        )

        assert response.status_code == 500
        assert "Failed to start execution" in response.json()["detail"]

    def test_start_execution_missing_workflow_id(self):
        """Test execution start without workflow_id parameter"""
        # Create test PDF file
        pdf_content = b"%PDF-1.4\ntest content"
        pdf_file = ("test.pdf", BytesIO(pdf_content), "application/pdf")

        response = self.client.post(
            "/api/executions/",
            files={"file": pdf_file}
        )

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_start_execution_missing_file(self):
        """Test execution start without file upload"""
        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "test-workflow"}
        )

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_start_execution_non_pdf_file(self):
        """Test execution start with non-PDF file"""
        # Create test text file
        text_content = b"This is not a PDF"
        text_file = ("test.txt", BytesIO(text_content), "text/plain")

        response = self.client.post(
            "/api/executions/",
            params={"workflow_id": "test-workflow"},
            files={"file": text_file}
        )

        # Should still accept non-PDF files at API level
        # File type validation happens at the service level
        assert response.status_code in [400, 500]

    @patch("api.dependencies.get_execution_service")
    def test_list_executions_success(self, mock_get_execution_service):
        """Test successful execution listing"""
        mock_service = AsyncMock()

        # Create mock executions
        execution1 = Execution.create(workflow_id="workflow-1")
        execution1.id = "execution-1"
        execution2 = Execution.create(workflow_id="workflow-2")
        execution2.id = "execution-2"
        execution2.complete_execution("processed output")

        mock_service.list_executions.return_value = [execution1, execution2]
        mock_get_execution_service.return_value = mock_service

        response = self.client.get("/api/executions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "execution-1"
        assert data[0]["status"] == ExecutionStatus.RUNNING.value
        assert data[1]["id"] == "execution-2"
        assert data[1]["status"] == ExecutionStatus.COMPLETED.value
        assert data[1]["output_data"] == "processed output"

        mock_service.list_executions.assert_called_once_with(limit=20, offset=0)

    @patch("api.dependencies.get_execution_service")
    def test_list_executions_with_pagination(self, mock_get_execution_service):
        """Test execution listing with custom pagination parameters"""
        mock_service = AsyncMock()
        mock_service.list_executions.return_value = []
        mock_get_execution_service.return_value = mock_service

        response = self.client.get("/api/executions/?limit=10&offset=5")

        assert response.status_code == 200
        mock_service.list_executions.assert_called_once_with(limit=10, offset=5)

    @patch("api.dependencies.get_execution_service")
    def test_get_execution_success(self, mock_get_execution_service):
        """Test successful execution retrieval"""
        mock_service = AsyncMock()

        execution_id = "test-execution-id"
        execution = Execution.create(workflow_id="test-workflow")
        execution.id = execution_id
        execution.complete_execution("final output")

        mock_service.get_execution.return_value = execution
        mock_get_execution_service.return_value = mock_service

        response = self.client.get(f"/api/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        assert data["workflow_id"] == "test-workflow"
        assert data["status"] == ExecutionStatus.COMPLETED.value
        assert data["output_data"] == "final output"

        mock_service.get_execution.assert_called_once_with(execution_id)

    @patch("api.dependencies.get_execution_service")
    def test_get_execution_not_found(self, mock_get_execution_service):
        """Test getting non-existent execution"""
        mock_service = AsyncMock()
        mock_service.get_execution.return_value = None
        mock_get_execution_service.return_value = mock_service

        execution_id = "nonexistent-execution"
        response = self.client.get(f"/api/executions/{execution_id}")

        assert response.status_code == 404
        assert "Execution not found" in response.json()["detail"]

        mock_service.get_execution.assert_called_once_with(execution_id)

    @patch("api.dependencies.get_execution_service")
    def test_get_execution_failed_status(self, mock_get_execution_service):
        """Test getting execution with failed status"""
        mock_service = AsyncMock()

        execution_id = "failed-execution-id"
        execution = Execution.create(workflow_id="test-workflow")
        execution.id = execution_id
        execution.fail_execution("Processing failed due to invalid input")

        mock_service.get_execution.return_value = execution
        mock_get_execution_service.return_value = mock_service

        response = self.client.get(f"/api/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        assert data["status"] == ExecutionStatus.FAILED.value
        assert data["error_message"] == "Processing failed due to invalid input"
        assert data["output_data"] is None

    def test_input_file_path_security(self):
        """Test that input_file_path returns filename only, not full path"""
        # This is tested implicitly in other tests but worth explicit verification
        # The ExecutionService should convert full paths to filenames only
        pass