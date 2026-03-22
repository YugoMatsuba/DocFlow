from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Query
from typing import List

from services.execution_service import ExecutionService
from api.schemas.execution import ExecutionResponse
from api.dependencies import get_execution_service
from infra.storage.file_storage import FileStorage
from config.logging import get_logger, log_request_data

router = APIRouter(prefix="/executions", tags=["executions"])
logger = get_logger("execution.router")

def get_file_storage() -> FileStorage:
    """Get file storage instance"""
    return FileStorage()

@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def start_execution(
    workflow_id: str = Query(..., description="Workflow ID to execute"),
    file: UploadFile = File(..., description="PDF file to process"),
    service: ExecutionService = Depends(get_execution_service),
    file_storage: FileStorage = Depends(get_file_storage),
):
    """Start workflow execution with PDF file upload"""
    # Log the incoming request
    log_request_data(
        logger,
        "POST /executions/",
        workflow_id=workflow_id,
        file_name=file.filename,
        file_content_type=file.content_type,
        file_size=file.size if hasattr(file, 'size') else 'unknown'
    )

    try:
        # Save the uploaded file
        file_path = await file_storage.save_pdf_file(file)
        logger.info(f"File saved successfully: {file_path}")

        # Create execution with file path
        execution = await service.start_execution(workflow_id, file_path)
        if not execution:
            # Clean up uploaded file if execution creation failed
            logger.warning(f"Execution creation failed, cleaning up file: {file_path}")
            file_storage.delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found or invalid"
            )

        logger.info(f"Execution {execution.id} accepted for background processing")

        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in start_execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start execution: {str(e)}"
        )

@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    limit: int = Query(20, description="Maximum number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    service: ExecutionService = Depends(get_execution_service)
):
    """List all executions with pagination"""
    executions = await service.list_executions(limit=limit, offset=offset)
    return executions

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get execution status"""
    execution = await service.get_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    return execution
