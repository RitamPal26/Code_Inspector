"""
Pydantic schemas for request/response validation.

This module defines all data models used for API requests, responses,
and internal state management. Uses Pydantic for automatic validation
and JSON serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal, Optional
from uuid import UUID
from datetime import datetime


# ============================================================================
# CONDITION MODELS (for loop and branching logic)
# ============================================================================

class SimpleCondition(BaseModel):
    """
    Simple comparison condition for state evaluation.
    
    Supports basic comparisons (==, !=, >, <, >=, <=) and collection
    operations (length, max, min, contains).
    
    Attributes:
        field: Dot-notation path to state field (e.g., "quality_score")
        operator: Comparison or collection operator
        comparator: Secondary operator for collection operations
        value: Value to compare against
        
    Example:
        {"field": "quality_score", "operator": ">=", "value": 8}
        {"field": "issues", "operator": "length", "comparator": "==", "value": 0}
    """
    
    field: str = Field(..., description="State field path (dot notation supported)")
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "length", "max", "min", "contains"] = Field(
        ...,
        description="Comparison or collection operator"
    )
    comparator: Optional[Literal["==", "!=", ">", "<", ">=", "<="]] = Field(
        None,
        description="Secondary operator for collection operations"
    )
    value: Any = Field(..., description="Comparison value")
    
    @field_validator("comparator")
    @classmethod
    def validate_comparator(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that comparator is only used with collection operators."""
        operator = info.data.get("operator")
        collection_ops = ["length", "max", "min"]
        
        if operator in collection_ops and v is None:
            raise ValueError(f"Comparator required when using {operator} operator")
        if operator not in collection_ops and v is not None:
            raise ValueError(f"Comparator not allowed with {operator} operator")
        
        return v


class ComplexCondition(BaseModel):
    """
    Complex nested condition with logical operators.
    
    Allows combining multiple conditions using AND, OR, NOT logic
    for sophisticated control flow.
    
    Attributes:
        type: Logical operator (AND/OR/NOT)
        conditions: List of simple or complex conditions to evaluate
        
    Example:
        {
            "type": "AND",
            "conditions": [
                {"field": "quality_score", "operator": ">=", "value": 8},
                {"field": "issues", "operator": "length", "comparator": "==", "value": 0}
            ]
        }
    """
    
    type: Literal["AND", "OR", "NOT"] = Field(..., description="Logical operator")
    conditions: list["SimpleCondition | ComplexCondition"] = Field(
        ...,
        min_length=1,
        description="List of conditions to evaluate"
    )
    
    @field_validator("conditions")
    @classmethod
    def validate_conditions_count(cls, v: list, info) -> list:
        """Validate condition count based on operator type."""
        condition_type = info.data.get("type")
        
        if condition_type == "NOT" and len(v) != 1:
            raise ValueError("NOT operator requires exactly 1 condition")
        if condition_type in ["AND", "OR"] and len(v) < 2:
            raise ValueError(f"{condition_type} operator requires at least 2 conditions")
        
        return v


# ============================================================================
# NODE AND GRAPH DEFINITION MODELS
# ============================================================================

class NodeDefinition(BaseModel):
    """
    Definition of a workflow node.
    
    Nodes can be either normal (single tool execution) or loop (repeated
    execution of multiple nodes until condition is met).
    
    Attributes:
        name: Unique node identifier
        type: Node type (normal or loop)
        tool_name: Tool to execute (for normal nodes)
        nodes: Child nodes (for loop nodes)
        loop_condition: Exit condition (for loop nodes)
        max_iterations: Maximum loop iterations
        on_max_reached: Behavior when max iterations reached
    """
    
    name: str = Field(..., description="Unique node name", min_length=1, max_length=255)
    type: Literal["normal", "loop"] = Field(default="normal", description="Node type")
    tool_name: Optional[str] = Field(None, description="Tool name for normal nodes")
    nodes: Optional[list[str]] = Field(None, description="Child node names for loop nodes")
    loop_condition: Optional[SimpleCondition | ComplexCondition] = Field(
        None,
        description="Exit condition for loop nodes"
    )
    max_iterations: Optional[int] = Field(
        15,
        ge=1,
        le=100,
        description="Maximum loop iterations"
    )
    on_max_reached: Optional[Literal["fail", "continue"]] = Field(
        "fail",
        description="Action when max iterations reached"
    )
    
    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure tool_name is provided for normal nodes."""
        node_type = info.data.get("type")
        if node_type == "normal" and not v:
            raise ValueError("tool_name required for normal nodes")
        return v
    
    @field_validator("nodes")
    @classmethod
    def validate_nodes(cls, v: Optional[list[str]], info) -> Optional[list[str]]:
        """Ensure nodes list is provided for loop nodes."""
        node_type = info.data.get("type")
        if node_type == "loop" and not v:
            raise ValueError("nodes list required for loop nodes")
        if node_type == "loop" and v and len(v) < 1:
            raise ValueError("loop nodes must contain at least 1 node")
        return v
    
    @field_validator("loop_condition")
    @classmethod
    def validate_loop_condition(cls, v: Optional[SimpleCondition | ComplexCondition], info) -> Optional[SimpleCondition | ComplexCondition]:
        """Ensure loop_condition is provided for loop nodes."""
        node_type = info.data.get("type")
        if node_type == "loop" and not v:
            raise ValueError("loop_condition required for loop nodes")
        return v


class EdgeDefinition(BaseModel):
    """
    Connection between two nodes.
    
    Edges define the flow of execution between nodes. Can include
    optional conditions for branching logic.
    
    Attributes:
        from_node: Source node name
        to_node: Target node name
        condition: Optional condition for conditional branching
    """
    
    from_node: str = Field(..., description="Source node name")
    to_node: str = Field(..., description="Target node name")
    condition: Optional[SimpleCondition | ComplexCondition] = Field(
        None,
        description="Condition for conditional edges"
    )


class GraphDefinition(BaseModel):
    """
    Complete workflow graph definition.
    
    Defines the structure of a workflow including all nodes, their
    connections, and the initial state schema.
    
    Attributes:
        nodes: List of node definitions
        edges: List of edge definitions
        initial_state_schema: Schema for initial state validation
    """
    
    nodes: list[NodeDefinition] = Field(..., min_length=1, description="Workflow nodes")
    edges: list[EdgeDefinition] = Field(..., description="Node connections")
    initial_state_schema: dict[str, str] = Field(
        ...,
        description="Initial state field types (field_name: type_name)"
    )
    
    @field_validator("nodes")
    @classmethod
    def validate_unique_node_names(cls, v: list[NodeDefinition]) -> list[NodeDefinition]:
        """Ensure all node names are unique."""
        names = [node.name for node in v]
        if len(names) != len(set(names)):
            raise ValueError("Node names must be unique")
        return v
    
    @field_validator("edges")
    @classmethod
    def validate_edge_references(cls, v: list[EdgeDefinition], info) -> list[EdgeDefinition]:
        """Ensure all edge references point to valid nodes."""
        nodes = info.data.get("nodes", [])
        node_names = {node.name for node in nodes}
        
        for edge in v:
            if edge.from_node not in node_names:
                raise ValueError(f"Edge references unknown from_node: {edge.from_node}")
            if edge.to_node not in node_names:
                raise ValueError(f"Edge references unknown to_node: {edge.to_node}")
        
        return v


# ============================================================================
# EXECUTION LOG MODELS
# ============================================================================

class ExecutionLog(BaseModel):
    """
    Single execution log entry.
    
    Records the result of executing a single node, including
    timing, status, and any relevant metadata.
    
    Attributes:
        timestamp: When the node executed
        node: Node name
        status: Execution status
        iteration: Current iteration (for loop nodes)
        message: Optional status message or error details
        duration_ms: Execution duration in milliseconds
    """
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    node: str = Field(..., description="Node name")
    status: Literal["success", "failed", "skipped"] = Field(..., description="Execution status")
    iteration: Optional[int] = Field(None, description="Iteration number for loop nodes")
    message: Optional[str] = Field(None, description="Status message or error details")
    duration_ms: Optional[int] = Field(None, ge=0, description="Execution duration in milliseconds")


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class CreateWorkflowRequest(BaseModel):
    """
    Request to create a new workflow.
    
    Attributes:
        name: Workflow name
        description: Optional workflow description
        graph_definition: Complete graph structure
    """
    
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    graph_definition: GraphDefinition = Field(..., description="Graph structure")


class CreateWorkflowResponse(BaseModel):
    """
    Response after creating a workflow.
    
    Attributes:
        workflow_id: Generated workflow identifier
        message: Success message
    """
    
    workflow_id: UUID = Field(..., description="Created workflow ID")
    message: str = Field(..., description="Success message")


class RunWorkflowRequest(BaseModel):
    """
    Request to execute a workflow.
    
    Attributes:
        workflow_id: Workflow to execute
        initial_state: Starting state for execution
    """
    
    workflow_id: UUID = Field(..., description="Workflow ID to execute")
    initial_state: dict[str, Any] = Field(..., description="Initial workflow state")


class RunWorkflowResponse(BaseModel):
    """
    Response when workflow execution starts.
    
    Attributes:
        run_id: Generated execution identifier
        status: Current status (always "running" initially)
        message: Status message
    """
    
    run_id: UUID = Field(..., description="Execution run ID")
    status: Literal["running"] = Field(default="running", description="Execution status")
    message: str = Field(..., description="Status message")


class WorkflowStateResponse(BaseModel):
    """
    Response for workflow state query.
    
    Provides complete status of a workflow execution including
    current state, logs, and any errors.
    
    Attributes:
        run_id: Execution identifier
        workflow_id: Parent workflow identifier
        status: Current execution status
        current_node: Currently executing node
        iteration_count: Current iteration count
        state: Current workflow state
        logs: Execution log entries
        error_message: Error details if failed
        started_at: Execution start time
        completed_at: Execution completion time
    """
    
    run_id: UUID = Field(..., description="Execution run ID")
    workflow_id: UUID = Field(..., description="Workflow ID")
    status: Literal["running", "completed", "failed"] = Field(..., description="Execution status")
    current_node: Optional[str] = Field(None, description="Currently executing node")
    iteration_count: int = Field(default=0, ge=0, description="Current iteration count")
    state: dict[str, Any] = Field(..., description="Current workflow state")
    logs: list[ExecutionLog] = Field(default_factory=list, description="Execution logs")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
