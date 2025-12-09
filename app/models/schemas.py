from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
from uuid import UUID
from datetime import datetime

# Node Definitions
class SimpleCondition(BaseModel):
    """Simple comparison condition"""
    field: str
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "length", "max", "min", "contains"]
    comparator: Optional[Literal["==", "!=", ">", "<", ">=", "<="]] = None
    value: Any

class ComplexCondition(BaseModel):
    """Complex nested condition with AND/OR"""
    type: Literal["AND", "OR", "NOT"]
    conditions: list[SimpleCondition | "ComplexCondition"]

class NodeDefinition(BaseModel):
    """Definition of a single node"""
    name: str
    type: Literal["normal", "loop"]
    tool_name: Optional[str] = None  # For normal nodes
    nodes: Optional[list[str]] = None  # For loop nodes
    loop_condition: Optional[SimpleCondition | ComplexCondition] = None
    max_iterations: Optional[int] = 15
    on_max_reached: Optional[Literal["fail", "continue"]] = "fail"

class EdgeDefinition(BaseModel):
    """Connection between nodes"""
    from_node: str
    to_node: str
    condition: Optional[SimpleCondition | ComplexCondition] = None

class GraphDefinition(BaseModel):
    """Complete workflow definition"""
    nodes: list[NodeDefinition]
    edges: list[EdgeDefinition]
    initial_state_schema: dict[str, str]  # Field name -> type

# API Request/Response Models
class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow"""
    name: str
    description: Optional[str] = None
    graph_definition: GraphDefinition

class CreateWorkflowResponse(BaseModel):
    """Response after workflow creation"""
    workflow_id: UUID
    message: str

class RunWorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_id: UUID
    initial_state: dict[str, Any]

class RunWorkflowResponse(BaseModel):
    """Response when workflow execution starts"""
    run_id: UUID
    status: Literal["running"]
    message: str

class ExecutionLog(BaseModel):
    """Single execution log entry"""
    timestamp: datetime
    node: str
    status: Literal["success", "failed", "skipped"]
    iteration: Optional[int] = None
    message: Optional[str] = None

class WorkflowStateResponse(BaseModel):
    """Response for workflow state query"""
    run_id: UUID
    workflow_id: UUID
    status: Literal["running", "completed", "failed"]
    current_node: Optional[str] = None
    iteration_count: int
    state: dict[str, Any]
    logs: list[ExecutionLog]
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
