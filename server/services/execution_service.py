from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.execution import Execution, ExecutionStatus
from domain.entities.workflow import Workflow
from domain.repositories.execution_repository import ExecutionRepository
from domain.repositories.workflow_repository import WorkflowRepository
from api.schemas.execution import ExecutionResponse
from domain.rules.workflow_rules import WorkflowRules
from config.logging import get_logger, log_request_data, log_execution_step
from services.execution_dispatcher import ExecutionDispatcher
from services.processors.registry import ProcessorRegistry

class ExecutionService:
    def __init__(
        self,
        execution_repository: ExecutionRepository,
        workflow_repository: WorkflowRepository,
        dispatcher: ExecutionDispatcher,
        db_session: AsyncSession,
    ):
        self.execution_repository = execution_repository
        self.workflow_repository = workflow_repository
        self.dispatcher = dispatcher
        self.db_session = db_session
        self.logger = get_logger("execution.service")

    async def start_execution(
        self,
        workflow_id: str,
        input_file_path: Optional[str] = None
    ) -> Optional[ExecutionResponse]:
        """Start workflow execution with file input"""
        # Log the execution request
        log_request_data(
            self.logger,
            "start_execution",
            workflow_id=workflow_id,
            input_file_path=input_file_path,
            has_file=input_file_path is not None
        )

        workflow = await self.workflow_repository.get_with_nodes(workflow_id)
        if not workflow:
            self.logger.warning(f"Workflow not found: {workflow_id}")
            return None

        # Log workflow details
        self.logger.info(f"Found workflow: {workflow.name} with {len(workflow.nodes)} nodes")
        for node in workflow.nodes:
            self.logger.debug(f"Node: {node.name} (type: {node.node_type}, order: {node.order})")

        validation_errors = WorkflowRules.validate_workflow(workflow)
        validation_errors.extend(self._validate_node_configurations(workflow.nodes))
        if validation_errors:
            self.logger.error(f"Workflow validation failed: {validation_errors}")
            return None

        execution = Execution.create(
            workflow_id=workflow_id,
            input_file_path=input_file_path
        )

        created_execution = await self.execution_repository.create(execution)
        await self.db_session.commit()
        self.logger.info(f"Created execution and committed transaction: {created_execution.id}")

        self.dispatcher.dispatch(created_execution.id, self.process_workflow_execution)
        self.logger.info(f"Dispatched background processing for execution: {created_execution.id}")

        return self._to_execution_response(created_execution)

    async def get_execution(self, execution_id: str) -> Optional[ExecutionResponse]:
        """Get execution status"""
        execution = await self.execution_repository.get_by_id(execution_id)
        if not execution:
            return None
        return self._to_execution_response(execution)

    async def list_executions(self, limit: int = 20, offset: int = 0) -> List[ExecutionResponse]:
        """List all executions with pagination"""
        executions = await self.execution_repository.list_all(limit=limit, offset=offset)
        return [self._to_execution_response(execution) for execution in executions]

    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        output_data: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[ExecutionResponse]:
        """Update execution status"""
        # Log status update request
        log_execution_step(
            self.logger,
            execution_id,
            "status_update",
            new_status=status.value,
            has_output_data=output_data is not None,
            has_error=error_message is not None,
            output_data_length=len(output_data) if output_data else 0
        )

        execution = await self.execution_repository.get_by_id(execution_id)
        if not execution:
            self.logger.warning(f"Execution not found for status update: {execution_id}")
            return None

        old_status = execution.status

        if status == ExecutionStatus.RUNNING:
            # Executions are already created as RUNNING, no action needed
            self.logger.info(f"Execution {execution_id} is running")
        elif status == ExecutionStatus.COMPLETED:
            execution.complete_execution(output_data)
            self.logger.info(f"Execution {execution_id} completed successfully with {len(output_data) if output_data else 0} chars output")
        elif status == ExecutionStatus.FAILED:
            execution.fail_execution(error_message)
            self.logger.error(f"Execution {execution_id} failed: {error_message}")

        updated_execution = await self.execution_repository.update(execution)
        self.logger.info(f"Execution {execution_id} status updated from {old_status} to {status}")

        return self._to_execution_response(updated_execution)

    async def process_workflow_execution(self, execution_id: str) -> None:
        """Run a workflow execution in the background."""
        exec_logger = get_logger("execution.processor")

        log_execution_step(
            exec_logger,
            execution_id,
            "background_processing_start",
            message="Starting background workflow execution processing"
        )

        try:
            execution_entity = await self.execution_repository.get_by_id(execution_id)
            if not execution_entity:
                exec_logger.error(f"Execution entity not found: {execution_id}")
                return

            log_execution_step(
                exec_logger,
                execution_id,
                "execution_retrieved",
                workflow_id=execution_entity.workflow_id,
                input_file_path=execution_entity.input_file_path,
                status=execution_entity.status.value
            )

            workflow = await self.workflow_repository.get_with_nodes(execution_entity.workflow_id)

            if not workflow or not workflow.nodes:
                exec_logger.error(f"Workflow {execution_entity.workflow_id} has no nodes to execute")
                await self.update_execution_status(
                    execution_id,
                    ExecutionStatus.FAILED,
                    error_message="Workflow has no nodes to execute"
                )
                return

            log_execution_step(
                exec_logger,
                execution_id,
                "workflow_loaded",
                workflow_name=workflow.name,
                node_count=len(workflow.nodes),
                node_types=[node.node_type.value for node in workflow.nodes]
            )

            current_data = execution_entity.input_file_path or ""
            exec_logger.info(
                "Starting node processing for execution %s with input: %s",
                execution_id,
                current_data,
            )

            for i, node in enumerate(sorted(workflow.nodes, key=lambda x: x.order), 1):
                log_execution_step(
                    exec_logger,
                    execution_id,
                    "node_processing_start",
                    node_name=node.name,
                    node_type=node.node_type.value,
                    node_order=node.order,
                    node_step=f"{i}/{len(workflow.nodes)}",
                    input_data_type=type(current_data).__name__,
                    input_data_length=len(str(current_data))
                )

                try:
                    processor = ProcessorRegistry.get_processor(node.node_type)
                    processor.validate_config(node.configuration)
                    result = await processor.process(current_data, node.configuration)

                    log_execution_step(
                        exec_logger,
                        execution_id,
                        "node_processing_complete",
                        node_name=node.name,
                        node_step=f"{i}/{len(workflow.nodes)}",
                        output_data_type=type(result).__name__,
                        output_data_length=len(str(result))
                    )

                    current_data = result

                except Exception as exc:
                    log_execution_step(
                        exec_logger,
                        execution_id,
                        "node_processing_failed",
                        node_name=node.name,
                        node_step=f"{i}/{len(workflow.nodes)}",
                        error=str(exc)
                    )

                    await self.update_execution_status(
                        execution_id,
                        ExecutionStatus.FAILED,
                        error_message=f"Error processing node {node.name}: {str(exc)}"
                    )
                    return

            log_execution_step(
                exec_logger,
                execution_id,
                "workflow_execution_complete",
                final_output_length=len(str(current_data)),
                nodes_processed=len(workflow.nodes)
            )

            await self.update_execution_status(
                execution_id,
                ExecutionStatus.COMPLETED,
                output_data=current_data
            )

        except Exception as exc:
            log_execution_step(
                exec_logger,
                execution_id,
                "workflow_execution_failed",
                error=str(exc)
            )

            await self.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                error_message=f"Execution failed: {str(exc)}"
            )

    def _validate_node_configurations(self, nodes: List["Node"]) -> List[str]:
        """Validate node configurations using processor-specific validators."""
        errors: List[str] = []

        for node in nodes:
            try:
                ProcessorRegistry.validate_config(node.node_type, node.configuration)
            except Exception as exc:
                errors.append(f"Node '{node.name}' configuration validation failed: {str(exc)}")

        return errors

    def _to_execution_response(self, execution: Execution) -> ExecutionResponse:
        """Convert domain entity to response DTO"""
        return ExecutionResponse(
            id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            input_file_path=execution.input_file_path,
            output_data=execution.output_data,
            error_message=execution.error_message,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
            completed_at=execution.completed_at
        )
