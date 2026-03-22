from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from domain.repositories.workflow_repository import WorkflowRepository
from domain.entities.workflow import Workflow
from domain.entities.node import Node
from domain.enums.node_type import NodeType
from ..models.workflow import WorkflowModel, NodeModel

class SQLAlchemyWorkflowRepository(WorkflowRepository):
    """SQLAlchemy implementation of WorkflowRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, workflow: Workflow) -> Workflow:
        """Create a new workflow"""
        db_workflow = WorkflowModel(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            is_active=workflow.is_active
        )

        # Add nodes if they exist
        for node in workflow.nodes:
            db_node = NodeModel(
                id=node.id,
                workflow_id=workflow.id,
                node_type=node.node_type.value,
                name=node.name,
                configuration=node.configuration,
                order=node.order
            )
            db_workflow.nodes.append(db_node)

        self.session.add(db_workflow)
        await self.session.flush()
        await self.session.refresh(db_workflow, ['nodes'])

        return self._to_domain(db_workflow)

    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID without nodes"""
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        result = await self.session.execute(stmt)
        db_workflow = result.scalar_one_or_none()

        return self._to_domain(db_workflow) if db_workflow else None

    async def get_with_nodes(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow with all its nodes loaded"""
        stmt = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.nodes))
            .where(WorkflowModel.id == workflow_id)
        )
        result = await self.session.execute(stmt)
        db_workflow = result.scalar_one_or_none()

        return self._to_domain(db_workflow) if db_workflow else None

    async def update(self, workflow: Workflow) -> Workflow:
        """Update an existing workflow"""
        stmt = (
            update(WorkflowModel)
            .where(WorkflowModel.id == workflow.id)
            .values(
                name=workflow.name,
                description=workflow.description,
                is_active=workflow.is_active
            )
            .returning(WorkflowModel)
        )
        result = await self.session.execute(stmt)
        db_workflow = result.scalar_one()

        return self._to_domain(db_workflow)

    async def delete(self, workflow_id: str) -> bool:
        """Delete workflow by ID"""
        stmt = delete(WorkflowModel).where(WorkflowModel.id == workflow_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Workflow]:
        """List all workflows with pagination"""
        stmt = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.nodes))
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_workflows = result.scalars().all()

        return [self._to_domain(wf) for wf in db_workflows]

    async def list_active(self, limit: int = 100, offset: int = 0) -> List[Workflow]:
        """List all active workflows"""
        stmt = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.nodes))
            .where(WorkflowModel.is_active == True)
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_workflows = result.scalars().all()

        return [self._to_domain(wf) for wf in db_workflows]

    async def get_by_name(self, name: str) -> Optional[Workflow]:
        """Get workflow by name"""
        stmt = select(WorkflowModel).where(WorkflowModel.name == name)
        result = await self.session.execute(stmt)
        db_workflow = result.scalar_one_or_none()

        return self._to_domain(db_workflow) if db_workflow else None

    async def add_node(self, workflow_id: str, node: Node) -> Node:
        """Add a node to a workflow"""
        db_node = NodeModel(
            id=node.id,
            workflow_id=workflow_id,
            node_type=node.node_type.value,
            name=node.name,
            configuration=node.configuration,
            order=node.order
        )

        self.session.add(db_node)
        await self.session.flush()
        await self.session.refresh(db_node)

        return self._node_to_domain(db_node)

    async def remove_node(self, workflow_id: str, node_id: str) -> bool:
        """Remove a node from a workflow"""
        stmt = delete(NodeModel).where(
            NodeModel.workflow_id == workflow_id,
            NodeModel.id == node_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def reorder_nodes(self, workflow_id: str, node_ids: List[str]) -> bool:
        """Reorder nodes in a workflow"""
        try:
            for i, node_id in enumerate(node_ids):
                stmt = (
                    update(NodeModel)
                    .where(
                        NodeModel.workflow_id == workflow_id,
                        NodeModel.id == node_id
                    )
                    .values(order=i)
                )
                await self.session.execute(stmt)
            return True
        except Exception:
            return False

    def _to_domain(self, db_workflow: WorkflowModel) -> Workflow:
        """Convert SQLAlchemy model to domain entity"""
        if not db_workflow:
            return None

        nodes = []
        if hasattr(db_workflow, 'nodes') and db_workflow.nodes:
            nodes = [self._node_to_domain(db_node) for db_node in db_workflow.nodes]

        return Workflow(
            id=db_workflow.id,
            name=db_workflow.name,
            description=db_workflow.description,
            nodes=nodes,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at,
            is_active=db_workflow.is_active
        )

    def _node_to_domain(self, db_node: NodeModel) -> Node:
        """Convert SQLAlchemy node model to domain entity"""
        return Node(
            id=db_node.id,
            name=db_node.name,
            workflow_id=db_node.workflow_id,
            node_type=NodeType(db_node.node_type),
            configuration=db_node.configuration,
            order=db_node.order,
            created_at=db_node.created_at
        )