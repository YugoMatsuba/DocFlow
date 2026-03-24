from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from services.workflow_service import WorkflowService
from api.schemas.workflow import CreateWorkflowRequest, AddNodeRequest, WorkflowResponse, NodeResponse
from api.dependencies import get_workflow_service
from infra.db.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from config.logging import get_logger, log_request_data

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = get_logger("workflow.router")

@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: CreateWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Create a new workflow"""
    try:
        workflow = await service.create_workflow(request)

        # Commit the workflow to database before returning response
        await db_session.commit()
        logger.info(f"Workflow {workflow.id} committed to database")

        return workflow
    except Exception as exc:
        logger.exception("Unexpected error while creating workflow")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow"
        ) from exc

@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    service: WorkflowService = Depends(get_workflow_service)
):
    """List all workflows"""
    try:
        workflows = await service.list_workflows()
        return workflows
    except Exception as exc:
        logger.exception("Unexpected error while listing workflows")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflows"
        ) from exc

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow with all nodes"""
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow

@router.post("/{workflow_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def add_node(
    workflow_id: str,
    request: AddNodeRequest,
    service: WorkflowService = Depends(get_workflow_service),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Add a node to workflow"""
    log_request_data(
        logger,
        "POST /workflows/{workflow_id}/nodes",
        workflow_id=workflow_id,
        node_name=request.name,
        node_type=request.node_type.value,
        configuration_keys=list(request.configuration.keys()),
        order=request.order,
    )

    try:
        node = await service.add_node(workflow_id, request)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Commit the node insert before returning success so the next read sees it.
        await db_session.commit()
        logger.info("Node %s committed to workflow %s", node.id, workflow_id)

        return node
    except ValueError as exc:
        logger.exception(
            "Node validation failed for workflow_id=%s node_type=%s node_name=%s",
            workflow_id,
            request.node_type.value,
            request.name,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Unexpected error while adding node for workflow_id=%s node_type=%s node_name=%s",
            workflow_id,
            request.node_type.value,
            request.name,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add node"
        ) from exc

@router.get("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: str,
    service: WorkflowService = Depends(get_workflow_service)
):
    """Validate workflow and return any errors"""
    errors = await service.validate_workflow(workflow_id)

    if errors and "Workflow not found" in errors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
