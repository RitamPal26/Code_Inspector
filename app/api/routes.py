"""
API route handlers for workflow engine.

Provides REST endpoints for creating workflows, executing them,
and querying execution status.
"""

import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import Workflow, WorkflowRun
from app.models.schemas import (
    CreateWorkflowRequest,
    CreateWorkflowResponse,
    RunWorkflowRequest,
    RunWorkflowResponse,
    WorkflowStateResponse,
    ExecutionLog
)
from app.core.graph_engine import GraphEngine


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/graph/create", response_model=CreateWorkflowResponse, tags=["Workflows"])
async def create_workflow(
    request: CreateWorkflowRequest,
    db: AsyncSession = Depends(get_db)
) -> CreateWorkflowResponse:
    """
    Create a new workflow definition.
    
    Stores the workflow graph definition including nodes, edges,
    and initial state schema for future execution.
    
    Args:
        request: Workflow creation request with graph definition
        db: Database session
        
    Returns:
        CreateWorkflowResponse: Created workflow ID and success message
        
    Raises:
        HTTPException: If workflow creation fails
        
    Example:
        ```
        {
            "name": "Code Review Workflow",
            "description": "Automated code review with quality checks",
            "graph_definition": {
                "nodes": [...],
                "edges": [...],
                "initial_state_schema": {"code": "str"}
            }
        }
        ```
    """
    try:
        logger.info(f"Creating workflow: {request.name}")
        
        # Create workflow record
        workflow = Workflow(
            name=request.name,
            description=request.description,
            graph_definition=request.graph_definition.model_dump()
        )
        
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"Workflow created successfully: {workflow.id}")
        
        return CreateWorkflowResponse(
            workflow_id=workflow.id,
            message=f"Workflow '{request.name}' created successfully"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/graph/list", tags=["Workflows"])
async def list_workflows(
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """
    List all workflows.
    
    Returns basic information about all registered workflows.
    
    Args:
        db: Database session
        
    Returns:
        list[dict]: List of workflow summaries
    """
    try:
        result = await db.execute(select(Workflow))
        workflows = result.scalars().all()
        
        return [
            {
                "workflow_id": str(wf.id),
                "name": wf.name,
                "description": wf.description,
                "created_at": wf.created_at.isoformat() if wf.created_at else None
            }
            for wf in workflows
        ]
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {str(e)}"
        )


# ============================================================================
# WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

async def _execute_workflow_background(
    workflow_id: UUID,
    run_id: UUID,
    initial_state: dict,
    db_session: AsyncSession
) -> None:
    """
    Background task for workflow execution.
    
    Executes workflow asynchronously and updates run status.
    
    Args:
        workflow_id: Workflow to execute
        run_id: Run identifier
        initial_state: Starting state
        db_session: Database session
    """
    try:
        logger.info(f"Starting background execution: run_id={run_id}")
        
        # Create graph engine
        engine = GraphEngine(db_session)
        
        # Execute workflow
        await engine.execute_workflow(
            workflow_id=workflow_id,
            run_id=run_id,
            initial_state=initial_state
        )
        
        logger.info(f"Background execution completed: run_id={run_id}")
        
    except Exception as e:
        logger.error(f"Background execution failed: run_id={run_id}, error={str(e)}", exc_info=True)
        # Error handling is done in graph engine


@router.post("/graph/run", response_model=RunWorkflowResponse, tags=["Execution"])
async def run_workflow(
    request: RunWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> RunWorkflowResponse:
    """
    Execute a workflow asynchronously.
    
    Starts workflow execution in the background and returns immediately
    with a run_id for status polling.
    
    Args:
        request: Execution request with workflow_id and initial_state
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        RunWorkflowResponse: Run ID and status
        
    Raises:
        HTTPException: If workflow not found or execution fails to start
        
    Example:
        ```
        {
            "workflow_id": "123e4567-e89b-12d3-a456-426614174000",
            "initial_state": {
                "code": "def hello(): pass",
                "quality_score": 0
            }
        }
        ```
    """
    try:
        logger.info(f"Received workflow run request: workflow_id={request.workflow_id}")
        
        # Verify workflow exists
        result = await db.execute(
            select(Workflow).where(Workflow.id == request.workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {request.workflow_id} not found"
            )
        
        # Create workflow run record
        workflow_run = WorkflowRun(
            workflow_id=request.workflow_id,
            status="running",
            current_state=request.initial_state,
            iteration_count=0,
            execution_logs=[]
        )
        
        db.add(workflow_run)
        await db.commit()
        await db.refresh(workflow_run)
        
        logger.info(f"Workflow run created: run_id={workflow_run.run_id}")
        
        # Start background execution
        background_tasks.add_task(
            _execute_workflow_background,
            request.workflow_id,
            workflow_run.run_id,
            request.initial_state,
            db
        )
        
        return RunWorkflowResponse(
            run_id=workflow_run.run_id,
            status="running",
            message="Workflow execution started. Use run_id to check status."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to start workflow execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow execution: {str(e)}"
        )


@router.get("/graph/state/{run_id}", response_model=WorkflowStateResponse, tags=["Execution"])
async def get_workflow_state(
    run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> WorkflowStateResponse:
    """
    Get current state of a workflow execution.
    
    Returns the current status, state, logs, and any errors for
    a running or completed workflow execution.
    
    Args:
        run_id: Workflow run identifier
        db: Database session
        
    Returns:
        WorkflowStateResponse: Complete execution state
        
    Raises:
        HTTPException: If run_id not found
        
    Example Response:
        ```
        {
            "run_id": "...",
            "workflow_id": "...",
            "status": "running",
            "current_node": "check_complexity",
            "iteration_count": 3,
            "state": {...},
            "logs": [...],
            "error_message": null,
            "started_at": "2025-12-09T10:00:00",
            "completed_at": null
        }
        ```
    """
    try:
        logger.debug(f"Fetching workflow state: run_id={run_id}")
        
        # Get workflow run
        result = await db.execute(
            select(WorkflowRun).where(WorkflowRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow run {run_id} not found"
            )
        
        # Parse execution logs
        logs = [ExecutionLog(**log) for log in run.execution_logs]
        
        return WorkflowStateResponse(
            run_id=run.run_id,
            workflow_id=run.workflow_id,
            status=run.status,
            current_node=run.current_node,
            iteration_count=run.iteration_count,
            state=run.current_state or {},
            logs=logs,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow state: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow state: {str(e)}"
        )


@router.get("/graph/runs", tags=["Execution"])
async def list_workflow_runs(
    workflow_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """
    List workflow runs with optional filtering.
    
    Args:
        workflow_id: Filter by workflow ID (optional)
        status: Filter by status (optional)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        list[dict]: List of workflow run summaries
    """
    try:
        query = select(WorkflowRun)
        
        if workflow_id:
            query = query.where(WorkflowRun.workflow_id == workflow_id)
        if status:
            query = query.where(WorkflowRun.status == status)
        
        query = query.order_by(WorkflowRun.started_at.desc()).limit(limit)
        
        result = await db.execute(query)
        runs = result.scalars().all()
        
        return [
            {
                "run_id": str(run.run_id),
                "workflow_id": str(run.workflow_id),
                "status": run.status,
                "current_node": run.current_node,
                "iteration_count": run.iteration_count,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            }
            for run in runs
        ]
        
    except Exception as e:
        logger.error(f"Failed to list workflow runs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflow runs: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """
    API health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "workflow-engine-api",
        "version": "1.0.0"
    }
