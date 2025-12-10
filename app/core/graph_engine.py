"""
Graph execution engine.

Core workflow engine that orchestrates node execution, handles loops,
evaluates conditions, and manages workflow state.
"""

import logging
from typing import Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Workflow, WorkflowRun
from app.models.schemas import (
    NodeDefinition,
    EdgeDefinition,
    GraphDefinition,
    SimpleCondition,
    ComplexCondition
)
from app.core.state_manager import StateManager
from app.core.condition_evaluator import ConditionEvaluator
from app.core.node_executor import NodeExecutor
from app.core.execution_logger import ExecutionLogger
from app.config import settings


logger = logging.getLogger(__name__)


class GraphEngine:
    """
    Workflow graph execution engine.
    
    Orchestrates workflow execution including node sequencing,
    loop handling, conditional branching, and state management.
    """
    
    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize graph engine.
        
        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session
    
    async def execute_workflow(
        self,
        workflow_id: UUID,
        run_id: UUID,
        initial_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow_id: Workflow to execute
            run_id: Execution run identifier
            initial_state: Starting state
            
        Returns:
            dict[str, Any]: Final workflow state
            
        Raises:
            Exception: If workflow execution fails
        """
        try:
            # Load workflow definition
            result = await self.db_session.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Parse graph definition
            graph_def = GraphDefinition(**workflow.graph_definition)
            
            # Initialize components
            state_manager = StateManager(initial_state)
            execution_logger = ExecutionLogger()
            condition_evaluator = ConditionEvaluator(state_manager)
            node_executor = NodeExecutor(state_manager, execution_logger)
            
            logger.info(f"Starting workflow execution: {workflow.name} (run_id: {run_id})")
            
            # Execute workflow
            await self._execute_graph(
                graph_def=graph_def,
                run_id=run_id,
                state_manager=state_manager,
                condition_evaluator=condition_evaluator,
                node_executor=node_executor,
                execution_logger=execution_logger
            )
            
            # Get final state
            final_state = state_manager.get_state()
            
            # Update run status to completed
            await self._update_run_status(
                run_id=run_id,
                status="completed",
                current_node=None,
                state=final_state,
                logs=execution_logger.get_logs_dict(),
                completed_at=datetime.utcnow()
            )
            
            logger.info(f"Workflow execution completed: run_id={run_id}")
            
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Update run status to failed
            await self._update_run_status(
                run_id=run_id,
                status="failed",
                error_message=error_msg,
                completed_at=datetime.utcnow()
            )
            
            raise
    
    async def _execute_graph(
        self,
        graph_def: GraphDefinition,
        run_id: UUID,
        state_manager: StateManager,
        condition_evaluator: ConditionEvaluator,
        node_executor: NodeExecutor,
        execution_logger: ExecutionLogger
    ) -> None:
        """
        Execute workflow graph nodes in sequence.
        
        Args:
            graph_def: Graph definition
            run_id: Execution run ID
            state_manager: State manager
            condition_evaluator: Condition evaluator
            node_executor: Node executor
            execution_logger: Execution logger
        """
        # Build adjacency map for traversal
        adjacency_map = self._build_adjacency_map(graph_def.edges)
        
        # Find starting node (node with no incoming edges)
        start_node = self._find_start_node(graph_def.nodes, graph_def.edges)
        
        if not start_node:
            raise ValueError("No starting node found (node with no incoming edges)")
        
        # Execute from start node
        await self._execute_from_node(
            node_name=start_node.name,
            nodes_dict={n.name: n for n in graph_def.nodes},
            adjacency_map=adjacency_map,
            run_id=run_id,
            state_manager=state_manager,
            condition_evaluator=condition_evaluator,
            node_executor=node_executor,
            execution_logger=execution_logger
        )
    
    async def _execute_from_node(
        self,
        node_name: str,
        nodes_dict: dict[str, NodeDefinition],
        adjacency_map: dict[str, list[tuple[str, SimpleCondition | ComplexCondition | None]]],
        run_id: UUID,
        state_manager: StateManager,
        condition_evaluator: ConditionEvaluator,
        node_executor: NodeExecutor,
        execution_logger: ExecutionLogger,
        visited: set[str] | None = None
    ) -> None:
        """
        Execute nodes starting from given node.
        
        Args:
            node_name: Starting node name
            nodes_dict: Dictionary of all nodes
            adjacency_map: Node connections
            run_id: Execution run ID
            state_manager: State manager
            condition_evaluator: Condition evaluator
            node_executor: Node executor
            execution_logger: Execution logger
            visited: Set of visited nodes (for cycle detection)
        """
        if visited is None:
            visited = set()
        
        # Check for cycles
        if node_name in visited:
            logger.warning(f"Cycle detected at node '{node_name}', skipping")
            return
        
        visited.add(node_name)
        
        # Get node definition
        node_def = nodes_dict.get(node_name)
        if not node_def:
            raise ValueError(f"Node '{node_name}' not found in graph")
        
        # Update current node in database
        await self._update_run_status(
            run_id=run_id,
            current_node=node_name,
            state=state_manager.get_state(),
            logs=execution_logger.get_logs_dict()
        )
        
        # Execute node based on type
        if node_def.type == "normal":
            await node_executor.execute_normal_node(
                node_name=node_def.name,
                tool_name=node_def.tool_name
            )
        elif node_def.type == "loop":
            await self._execute_loop_node(
                node_def=node_def,
                nodes_dict=nodes_dict,
                adjacency_map=adjacency_map,
                run_id=run_id,
                state_manager=state_manager,
                condition_evaluator=condition_evaluator,
                node_executor=node_executor,
                execution_logger=execution_logger
            )
        else:
            raise ValueError(f"Unknown node type: {node_def.type}")
        
        # Find next nodes
        next_nodes = adjacency_map.get(node_name, [])
        
        # Execute next nodes
        for next_node_name, condition in next_nodes:
            # Check condition if present
            if condition:
                if condition_evaluator.evaluate(condition):
                    logger.info(f"Condition met for edge {node_name} -> {next_node_name}")
                    await self._execute_from_node(
                        node_name=next_node_name,
                        nodes_dict=nodes_dict,
                        adjacency_map=adjacency_map,
                        run_id=run_id,
                        state_manager=state_manager,
                        condition_evaluator=condition_evaluator,
                        node_executor=node_executor,
                        execution_logger=execution_logger,
                        visited=visited.copy()  # New path, copy visited set
                    )
                else:
                    logger.info(f"Condition not met for edge {node_name} -> {next_node_name}, skipping")
            else:
                # No condition, execute next node
                await self._execute_from_node(
                    node_name=next_node_name,
                    nodes_dict=nodes_dict,
                    adjacency_map=adjacency_map,
                    run_id=run_id,
                    state_manager=state_manager,
                    condition_evaluator=condition_evaluator,
                    node_executor=node_executor,
                    execution_logger=execution_logger,
                    visited=visited.copy()
                )
    
    async def _execute_loop_node(
        self,
        node_def: NodeDefinition,
        nodes_dict: dict[str, NodeDefinition],
        adjacency_map: dict[str, list[tuple[str, SimpleCondition | ComplexCondition | None]]],
        run_id: UUID,
        state_manager: StateManager,
        condition_evaluator: ConditionEvaluator,
        node_executor: NodeExecutor,
        execution_logger: ExecutionLogger
    ) -> None:
        """
        Execute a loop node with iteration and condition checking.
        
        Args:
            node_def: Loop node definition
            nodes_dict: Dictionary of all nodes
            adjacency_map: Node connections
            run_id: Execution run ID
            state_manager: State manager
            condition_evaluator: Condition evaluator
            node_executor: Node executor
            execution_logger: Execution logger
            
        Raises:
            RuntimeError: If max iterations reached without meeting exit condition
        """
        logger.info(f"Starting loop node '{node_def.name}' (max iterations: {node_def.max_iterations})")
        
        iteration = 0
        max_iterations = node_def.max_iterations or settings.max_loop_iterations
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Loop '{node_def.name}' iteration {iteration}/{max_iterations}")
            
            # Update iteration count in database
            await self._update_run_status(
                run_id=run_id,
                iteration_count=iteration,
                current_node=f"{node_def.name} (iteration {iteration})",
                state=state_manager.get_state(),
                logs=execution_logger.get_logs_dict()
            )
            
            # Execute all nodes in loop
            for child_node_name in node_def.nodes:
                child_node = nodes_dict.get(child_node_name)
                
                if not child_node:
                    raise ValueError(f"Loop child node '{child_node_name}' not found in nodes dictionary")
                
                # Execute child node
                if child_node.type == "normal":
                    await node_executor.execute_normal_node(
                        node_name=child_node.name,
                        tool_name=child_node.tool_name,
                        iteration=iteration
                    )
                else:
                    raise ValueError(f"Nested loop nodes not supported: {child_node_name}")
                
                # Update database after each child node execution
                await self._update_run_status(
                    run_id=run_id,
                    current_node=f"{node_def.name} (iteration {iteration}) - {child_node_name}",
                    state=state_manager.get_state(),
                    logs=execution_logger.get_logs_dict()
                )
            
            # Check exit condition after all loop nodes execute
            condition_met = condition_evaluator.evaluate(node_def.loop_condition)
            
            logger.info(f"Loop condition evaluated to: {condition_met} (quality_score: {state_manager.get_field('quality_score', 0)})")
            
            if condition_met:
                logger.info(f"Loop '{node_def.name}' exit condition met after {iteration} iterations")
                return
        
        # Max iterations reached
        logger.warning(f"Loop '{node_def.name}' reached max iterations ({max_iterations})")
        
        if node_def.on_max_reached == "fail":
            error_msg = f"Loop '{node_def.name}' failed: max iterations ({max_iterations}) reached without meeting exit condition"
            execution_logger.log_node_execution(
                node=node_def.name,
                status="failed",
                iteration=iteration,
                message=error_msg
            )
            raise RuntimeError(error_msg)
        else:
            # Continue execution
            logger.info(f"Loop '{node_def.name}' continuing despite max iterations")
    
    def _build_adjacency_map(
        self,
        edges: list[EdgeDefinition]
    ) -> dict[str, list[tuple[str, SimpleCondition | ComplexCondition | None]]]:
        """
        Build adjacency map from edges.
        
        Args:
            edges: List of edge definitions
            
        Returns:
            dict: Adjacency map {from_node: [(to_node, condition), ...]}
        """
        adjacency_map: dict[str, list[tuple[str, SimpleCondition | ComplexCondition | None]]] = {}
        
        for edge in edges:
            if edge.from_node not in adjacency_map:
                adjacency_map[edge.from_node] = []
            adjacency_map[edge.from_node].append((edge.to_node, edge.condition))
        
        return adjacency_map
    
    def _find_start_node(
        self,
        nodes: list[NodeDefinition],
        edges: list[EdgeDefinition]
    ) -> NodeDefinition | None:
        """
        Find the starting node (node with no incoming edges).
        
        Args:
            nodes: List of all nodes
            edges: List of edges
            
        Returns:
            NodeDefinition: Starting node or None
        """
        # Get all nodes that have incoming edges
        nodes_with_incoming = {edge.to_node for edge in edges}
        
        # Find first node without incoming edge
        for node in nodes:
            if node.name not in nodes_with_incoming:
                return node
        
        return None
    
    async def _update_run_status(
        self,
        run_id: UUID,
        status: str | None = None,
        current_node: str | None = None,
        state: dict[str, Any] | None = None,
        iteration_count: int | None = None,
        logs: list[dict[str, Any]] | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None
    ) -> None:
        """
        Update workflow run status in database.
        
        Args:
            run_id: Run identifier
            status: Execution status
            current_node: Currently executing node
            state: Current workflow state
            iteration_count: Current iteration count
            logs: Execution logs
            error_message: Error message if failed
            completed_at: Completion timestamp
        """
        updates = {}
        
        if status is not None:
            updates["status"] = status
        if current_node is not None:
            updates["current_node"] = current_node
        if state is not None:
            updates["current_state"] = state
        if iteration_count is not None:
            updates["iteration_count"] = iteration_count
        if logs is not None:
            updates["execution_logs"] = logs
        if error_message is not None:
            updates["error_message"] = error_message
        if completed_at is not None:
            updates["completed_at"] = completed_at
        
        if updates:
            await self.db_session.execute(
                update(WorkflowRun)
                .where(WorkflowRun.run_id == run_id)
                .values(**updates)
            )
            await self.db_session.commit()
