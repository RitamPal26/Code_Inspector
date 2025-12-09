"""
Execution logging utility.

Provides structured logging for workflow execution tracking.
Records node execution, timing, and status information.
"""

import logging
from datetime import datetime
from typing import Any, Literal
from app.models.schemas import ExecutionLog


logger = logging.getLogger(__name__)


class ExecutionLogger:
    """
    Manages execution logs for workflow runs.
    
    Tracks execution of individual nodes including timing, status,
    and any errors encountered during execution.
    """
    
    def __init__(self) -> None:
        """Initialize execution logger with empty log list."""
        self.logs: list[ExecutionLog] = []
    
    def log_node_execution(
        self,
        node: str,
        status: Literal["success", "failed", "skipped"],
        iteration: int | None = None,
        message: str | None = None,
        duration_ms: int | None = None
    ) -> ExecutionLog:
        """
        Log execution of a single node.
        
        Args:
            node: Node name
            status: Execution status
            iteration: Current iteration number (for loop nodes)
            message: Optional status message or error details
            duration_ms: Execution duration in milliseconds
            
        Returns:
            ExecutionLog: Created log entry
        """
        log_entry = ExecutionLog(
            timestamp=datetime.utcnow(),
            node=node,
            status=status,
            iteration=iteration,
            message=message,
            duration_ms=duration_ms
        )
        
        self.logs.append(log_entry)
        
        # Also log to Python logger
        log_level = logging.INFO if status == "success" else logging.ERROR
        logger.log(
            log_level,
            f"Node '{node}' {status}" + 
            (f" (iteration {iteration})" if iteration is not None else "") +
            (f": {message}" if message else "")
        )
        
        return log_entry
    
    def get_logs(self) -> list[ExecutionLog]:
        """
        Get all execution logs.
        
        Returns:
            list[ExecutionLog]: All log entries
        """
        return self.logs
    
    def get_logs_dict(self) -> list[dict[str, Any]]:
        """
        Get logs as dictionary list for JSON serialization.
        
        Returns:
            list[dict[str, Any]]: Logs in dictionary format
        """
        return [log.model_dump() for log in self.logs]
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.logs = []
        logger.debug("Execution logs cleared")
