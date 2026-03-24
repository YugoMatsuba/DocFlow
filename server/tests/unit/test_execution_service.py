import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from domain.entities.execution import Execution, ExecutionStatus
from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.enums.node_type import NodeType
from services.execution_service import ExecutionService
from errors import NotFoundError, ValidationError, ProcessingError
from services.processors.registry import ProcessorRegistry


class TestExecutionService:
    """Test cases for ExecutionService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_execution_repository = AsyncMock()
        self.mock_workflow_repository = AsyncMock()
        self.mock_dispatcher = MagicMock()
        self.mock_db_session = AsyncMock()

        self.service = ExecutionService(
            execution_repository=self.mock_execution_repository,
            workflow_repository=self.mock_workflow_repository,
            dispatcher=self.mock_dispatcher,
            db_session=self.mock_db_session
        )

    @pytest.mark.asyncio
    async def test_start_execution_workflow_not_found(self):
        """Test starting execution when workflow does not exist"""
        workflow_id = "nonexistent-workflow"
        self.mock_workflow_repository.get_with_nodes.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await self.service.start_execution(workflow_id)

        assert "Workflow not found" in str(exc_info.value)
        self.mock_workflow_repository.get_with_nodes.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_start_execution_workflow_validation_error(self):
        """Test starting execution when workflow has validation errors"""
        workflow_id = "test-workflow"
        workflow = Workflow.create("Invalid Workflow")
        # Create workflow with no nodes (will cause validation error)

        self.mock_workflow_repository.get_with_nodes.return_value = workflow

        with pytest.raises(ValidationError) as exc_info:
            await self.service.start_execution(workflow_id)

        assert "Workflow is invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_execution_success(self):
        """Test successful execution start"""
        workflow_id = "test-workflow"
        input_file_path = "test.pdf"

        # Create valid workflow
        workflow = Workflow.create("Test Workflow")
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        created_execution = Execution.create(workflow_id=workflow_id, input_file_path=input_file_path)

        self.mock_workflow_repository.get_with_nodes.return_value = workflow
        self.mock_execution_repository.create.return_value = created_execution

        with patch.object(ProcessorRegistry, 'validate_config'):
            result = await self.service.start_execution(workflow_id, input_file_path)

        assert result.id == created_execution.id
        assert result.workflow_id == workflow_id
        assert result.input_file_path == "test.pdf"  # Should return filename only

        self.mock_execution_repository.create.assert_called_once()
        self.mock_db_session.commit.assert_called_once()
        self.mock_dispatcher.dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_execution_create_failure(self):
        """Test execution start when database creation fails"""
        workflow_id = "test-workflow"

        workflow = Workflow.create("Test Workflow")
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        self.mock_workflow_repository.get_with_nodes.return_value = workflow
        self.mock_execution_repository.create.side_effect = Exception("DB Error")

        with patch.object(ProcessorRegistry, 'validate_config'):
            with pytest.raises(ProcessingError) as exc_info:
                await self.service.start_execution(workflow_id)

            assert "Failed to start execution" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_execution_dispatch_failure(self):
        """Test execution start when dispatch fails"""
        workflow_id = "test-workflow"

        workflow = Workflow.create("Test Workflow")
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        created_execution = Execution.create(workflow_id=workflow_id)

        self.mock_workflow_repository.get_with_nodes.return_value = workflow
        self.mock_execution_repository.create.return_value = created_execution
        self.mock_dispatcher.dispatch.side_effect = Exception("Dispatch Error")

        with patch.object(ProcessorRegistry, 'validate_config'):
            with patch.object(self.service, 'update_execution_status') as mock_update:
                with pytest.raises(ProcessingError) as exc_info:
                    await self.service.start_execution(workflow_id)

                assert "Failed to start execution" in str(exc_info.value)
                # Should also update execution status to FAILED
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_execution_exists(self):
        """Test getting an existing execution"""
        execution_id = "test-execution"
        execution = Execution.create(workflow_id="test-workflow")
        execution.id = execution_id

        self.mock_execution_repository.get_by_id.return_value = execution

        result = await self.service.get_execution(execution_id)

        assert result is not None
        assert result.id == execution_id
        self.mock_execution_repository.get_by_id.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self):
        """Test getting a non-existent execution"""
        execution_id = "nonexistent-execution"
        self.mock_execution_repository.get_by_id.return_value = None

        result = await self.service.get_execution(execution_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_executions(self):
        """Test listing executions"""
        executions = [
            Execution.create(workflow_id="workflow-1"),
            Execution.create(workflow_id="workflow-2")
        ]
        self.mock_execution_repository.list_all.return_value = executions

        result = await self.service.list_executions(limit=10, offset=0)

        assert len(result) == 2
        self.mock_execution_repository.list_all.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_update_execution_status_completed(self):
        """Test updating execution status to completed"""
        execution_id = "test-execution"
        output_data = "processed output"
        execution = Execution.create(workflow_id="test-workflow")
        execution.id = execution_id

        self.mock_execution_repository.get_by_id.return_value = execution
        self.mock_execution_repository.update.return_value = execution

        result = await self.service.update_execution_status(
            execution_id,
            ExecutionStatus.COMPLETED,
            output_data=output_data
        )

        assert result is not None
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.output_data == output_data
        self.mock_execution_repository.update.assert_called_once_with(execution)

    @pytest.mark.asyncio
    async def test_update_execution_status_failed(self):
        """Test updating execution status to failed"""
        execution_id = "test-execution"
        error_message = "Something went wrong"
        execution = Execution.create(workflow_id="test-workflow")
        execution.id = execution_id

        self.mock_execution_repository.get_by_id.return_value = execution
        self.mock_execution_repository.update.return_value = execution

        result = await self.service.update_execution_status(
            execution_id,
            ExecutionStatus.FAILED,
            error_message=error_message
        )

        assert result is not None
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == error_message
        self.mock_execution_repository.update.assert_called_once_with(execution)

    @pytest.mark.asyncio
    async def test_update_execution_status_not_found(self):
        """Test updating status of non-existent execution"""
        execution_id = "nonexistent-execution"
        self.mock_execution_repository.get_by_id.return_value = None

        result = await self.service.update_execution_status(
            execution_id,
            ExecutionStatus.COMPLETED
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_process_workflow_execution_success(self):
        """Test successful workflow execution processing"""
        execution_id = "test-execution"
        execution = Execution.create(workflow_id="test-workflow", input_file_path="test.pdf")

        workflow = Workflow.create("Test Workflow")
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        formatter_node = Node.create(
            name="Format",
            node_type=NodeType.FORMATTER,
            configuration={"format_type": "uppercase"},
            workflow_id=workflow.id,
            order=1
        )
        workflow.nodes.extend([extract_node, formatter_node])

        self.mock_execution_repository.get_by_id.return_value = execution
        self.mock_workflow_repository.get_with_nodes.return_value = workflow

        # Mock processors
        mock_extract_processor = AsyncMock()
        mock_extract_processor.process.return_value = "extracted text"
        mock_extract_processor.validate_config.return_value = None

        mock_formatter_processor = AsyncMock()
        mock_formatter_processor.process.return_value = "EXTRACTED TEXT"
        mock_formatter_processor.validate_config.return_value = None

        with patch.object(ProcessorRegistry, 'get_processor') as mock_get_processor:
            mock_get_processor.side_effect = [mock_extract_processor, mock_formatter_processor]

            with patch.object(self.service, 'update_execution_status') as mock_update:
                await self.service.process_workflow_execution(execution_id)

                # Should complete execution with final output
                mock_update.assert_called_with(
                    execution_id,
                    ExecutionStatus.COMPLETED,
                    output_data="EXTRACTED TEXT"
                )

    @pytest.mark.asyncio
    async def test_process_workflow_execution_not_found(self):
        """Test workflow execution processing when execution not found"""
        execution_id = "nonexistent-execution"
        self.mock_execution_repository.get_by_id.return_value = None

        await self.service.process_workflow_execution(execution_id)

        # Should return early without processing

    @pytest.mark.asyncio
    async def test_process_workflow_execution_no_nodes(self):
        """Test workflow execution processing when workflow has no nodes"""
        execution_id = "test-execution"
        execution = Execution.create(workflow_id="test-workflow")
        workflow = Workflow.create("Empty Workflow")

        self.mock_execution_repository.get_by_id.return_value = execution
        self.mock_workflow_repository.get_with_nodes.return_value = workflow

        with patch.object(self.service, 'update_execution_status') as mock_update:
            await self.service.process_workflow_execution(execution_id)

            # Should fail execution
            mock_update.assert_called_with(
                execution_id,
                ExecutionStatus.FAILED,
                error_message="Workflow has no nodes to execute"
            )

    @pytest.mark.asyncio
    async def test_process_workflow_execution_node_processing_failure(self):
        """Test workflow execution processing when node processing fails"""
        execution_id = "test-execution"
        execution = Execution.create(workflow_id="test-workflow", input_file_path="test.pdf")

        workflow = Workflow.create("Test Workflow")
        extract_node = Node.create(
            name="Extract",
            node_type=NodeType.EXTRACT_TEXT,
            configuration={},
            workflow_id=workflow.id,
            order=0
        )
        workflow.nodes.append(extract_node)

        self.mock_execution_repository.get_by_id.return_value = execution
        self.mock_workflow_repository.get_with_nodes.return_value = workflow

        # Mock processor that fails
        mock_processor = AsyncMock()
        mock_processor.validate_config.return_value = None
        mock_processor.process.side_effect = Exception("Processing failed")

        with patch.object(ProcessorRegistry, 'get_processor', return_value=mock_processor):
            with patch.object(self.service, 'update_execution_status') as mock_update:
                await self.service.process_workflow_execution(execution_id)

                # Should fail execution with node error
                mock_update.assert_called_once()
                call_args = mock_update.call_args
                assert call_args[0][0] == execution_id
                assert call_args[0][1] == ExecutionStatus.FAILED
                assert "Node 'Extract' failed" in call_args[1]["error_message"]

    def test_validate_node_configurations_valid(self):
        """Test node configuration validation with valid configurations"""
        nodes = [
            Node.create(
                name="Extract",
                node_type=NodeType.EXTRACT_TEXT,
                configuration={},
                workflow_id="test-workflow",
                order=0
            ),
            Node.create(
                name="Format",
                node_type=NodeType.FORMATTER,
                configuration={"format_type": "uppercase"},
                workflow_id="test-workflow",
                order=1
            )
        ]

        with patch.object(ProcessorRegistry, 'validate_config') as mock_validate:
            errors = self.service._validate_node_configurations(nodes)

            assert len(errors) == 0
            assert mock_validate.call_count == 2

    def test_validate_node_configurations_invalid(self):
        """Test node configuration validation with invalid configuration"""
        nodes = [
            Node.create(
                name="Format",
                node_type=NodeType.FORMATTER,
                configuration={"invalid_key": "value"},
                workflow_id="test-workflow",
                order=0
            )
        ]

        with patch.object(ProcessorRegistry, 'validate_config') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid config")

            errors = self.service._validate_node_configurations(nodes)

            assert len(errors) == 1
            assert "Node 'Format' configuration validation failed" in errors[0]

    def test_to_public_file_name(self):
        """Test conversion of file path to public file name"""
        # Test with full path
        result = self.service._to_public_file_name("/path/to/test.pdf")
        assert result == "test.pdf"

        # Test with None
        result = self.service._to_public_file_name(None)
        assert result is None

        # Test with invalid path (should return original)
        with patch('pathlib.Path') as mock_path:
            mock_path.side_effect = Exception("Invalid path")
            result = self.service._to_public_file_name("invalid/path")
            assert result == "invalid/path"