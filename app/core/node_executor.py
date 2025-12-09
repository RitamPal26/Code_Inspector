"""
Node execution logic.

Handles execution of individual nodes including tool invocation,
error handling, and timing.
"""

import logging
import time
from typing import Any
from uuid import UUID

from app.tools.tool_registry import tool_registry
from app.core.state_manager import StateManager
from app.core.execution_logger import ExecutionLogger


logger = logging.getLogger(__name__)


class NodeExecutor:
    """
    Executes individual workflow nodes.
    
    Handles tool invocation, error handling, timing, and logging
    for both normal and loop node types.
    """
    
    def __init__(
        self,
        state_manager: StateManager,
        execution_logger: ExecutionLogger
    ) -> None:
        """
        Initialize node executor.
        
        Args:
            state_manager: State manager for workflow state
            execution_logger: Logger for execution tracking
        """
        self.state_manager = state_manager
        self.execution_logger = execution_logger
    
    async def execute_normal_node(
        self,
        node_name: str,
        tool_name: str,
        iteration: int | None = None
    ) -> dict[str, Any]:
        """
        Execute a normal node (single tool execution).
        
        Args:
            node_name: Name of the node
            tool_name: Name of tool to execute
            iteration: Current iteration (for loop nodes)
            
        Returns:
            dict[str, Any]: Updated state after execution
            
        Raises:
            KeyError: If tool not found in registry
            Exception: If tool execution fails
        """
        start_time = time.time()
        
        try:
            # Get tool from registry
            if not tool_registry.exists(tool_name):
                raise KeyError(f"Tool '{tool_name}' not found in registry")
            
            tool_func = tool_registry.get(tool_name)
            
            # Get current state
            current_state = self.state_manager.get_state()
            
            logger.info(f"Executing node '{node_name}' with tool '{tool_name}'")
            
            # Execute tool
            updated_state = await tool_func(current_state)
            
            # Validate tool returned a dict
            if not isinstance(updated_state, dict):
                raise TypeError(f"Tool '{tool_name}' must return dict, got {type(updated_state)}")
            
            # Update state
            self.state_manager.set_state(updated_state, node_name)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log success
            self.execution_logger.log_node_execution(
                node=node_name,
                status="success",
                iteration=iteration,
                message=f"Tool '{tool_name}' executed successfully",
                duration_ms=duration_ms
            )
            
            logger.info(f"Node '{node_name}' completed in {duration_ms}ms")
            
            return updated_state
            
        except KeyError as e:
            # Tool not found
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Tool not found: {str(e)}"
            
            self.execution_logger.log_node_execution(
                node=node_name,
                status="failed",
                iteration=iteration,
                message=error_msg,
                duration_ms=duration_ms
            )
            
            logger.error(f"Node '{node_name}' failed: {error_msg}")
            raise
            
        except Exception as e:
            # Tool execution error
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Execution error: {str(e)}"
            
            self.execution_logger.log_node_execution(
                node=node_name,
                status="failed",
                iteration=iteration,
                message=error_msg,
                duration_ms=duration_ms
            )
            
            logger.error(f"Node '{node_name}' failed: {error_msg}", exc_info=True)
            raise
    
    async def skip_node(self, node_name: str, reason: str) -> None:
        """
        Mark a node as skipped.
        
        Args:
            node_name: Name of the node
            reason: Reason for skipping
        """
        self.execution_logger.log_node_execution(
            node=node_name,
            status="skipped",
            message=reason
        )
        
        logger.info(f"Node '{node_name}' skipped: {reason}")
    
    def __repr__(self) -> str:
        """String representation of node executor."""
        return f"<NodeExecutor(state_fields={len(self.state_manager.current_state)})>"
