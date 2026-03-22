from typing import List, Optional

from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.repositories.workflow_repository import WorkflowRepository
from api.schemas.workflow import CreateWorkflowRequest, AddNodeRequest, WorkflowResponse, NodeResponse
from domain.rules.workflow_rules import WorkflowRules
from services.processors.registry import ProcessorRegistry

class WorkflowService:
    def __init__(self, workflow_repository: WorkflowRepository):
        self.workflow_repository = workflow_repository

    async def create_workflow(self, request: CreateWorkflowRequest) -> WorkflowResponse:
        """Create a new workflow"""
        workflow = Workflow.create(
            name=request.name,
            description=request.description
        )

        created_workflow = await self.workflow_repository.create(workflow)
        return self._to_workflow_response(created_workflow)

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Get workflow with all nodes"""
        workflow = await self.workflow_repository.get_with_nodes(workflow_id)
        if not workflow:
            return None
        return self._to_workflow_response(workflow)

    async def list_workflows(self) -> List[WorkflowResponse]:
        """List all workflows"""
        workflows = await self.workflow_repository.list_all()
        return [self._to_workflow_response(workflow) for workflow in workflows]

    async def add_node(self, workflow_id: str, request: AddNodeRequest) -> Optional[NodeResponse]:
        """Add a node to a workflow"""
        workflow = await self.workflow_repository.get_with_nodes(workflow_id)
        if not workflow:
            return None

        ProcessorRegistry.validate_config(request.node_type, request.configuration)

        node = Node.create(
            name=request.name,
            node_type=request.node_type,
            configuration=request.configuration,
            workflow_id=workflow_id,
            order=request.order if request.order is not None else len(workflow.nodes)
        )

        created_node = await self.workflow_repository.add_node(workflow_id, node)
        return self._to_node_response(created_node)

    async def validate_workflow(self, workflow_id: str) -> List[str]:
        """Validate workflow and return list of errors"""
        workflow = await self.workflow_repository.get_with_nodes(workflow_id)
        if not workflow:
            return ["Workflow not found"]

        errors = WorkflowRules.validate_workflow(workflow)
        errors.extend(self._validate_node_configurations(workflow.nodes))
        return errors

    def _validate_node_configurations(self, nodes: List[Node]) -> List[str]:
        """Validate node configurations using processor-specific validators."""
        errors: List[str] = []

        for node in nodes:
            try:
                ProcessorRegistry.validate_config(node.node_type, node.configuration)
            except Exception as exc:
                errors.append(f"Node '{node.name}' configuration validation failed: {str(exc)}")

        return errors

    def _to_workflow_response(self, workflow: Workflow) -> WorkflowResponse:
        """Convert domain entity to response DTO"""
        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            nodes=[self._to_node_response(node) for node in workflow.nodes],
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            is_active=workflow.is_active
        )

    def _to_node_response(self, node: Node) -> NodeResponse:
        """Convert node domain entity to response DTO"""
        return NodeResponse(
            id=node.id,
            name=node.name,
            node_type=node.node_type,
            configuration=node.configuration,
            order=node.order,
            created_at=node.created_at
        )
