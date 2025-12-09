"""
Tool registry for workflow nodes.

Manages registration, storage, and retrieval of tools (Python functions)
that can be executed by workflow nodes.
"""

import logging
from typing import Any, Callable, Awaitable
from collections.abc import Coroutine


logger = logging.getLogger(__name__)


# Type alias for tool functions
ToolFunction = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ToolRegistry:
    """
    Registry for workflow tools.
    
    Stores and manages async Python functions that can be executed
    by workflow nodes. Each tool must accept and return a state dictionary.
    
    Tool Signature:
        async def tool_name(state: dict[str, Any]) -> dict[str, Any]:
            # Transform state
            return updated_state
    """
    
    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, ToolFunction] = {}
        logger.info("Tool registry initialized")
    
    def register(
        self,
        name: str,
        func: ToolFunction,
        overwrite: bool = False
    ) -> None:
        """
        Register a tool function.
        
        Args:
            name: Unique tool identifier
            func: Async function to register
            overwrite: Allow overwriting existing tool
            
        Raises:
            ValueError: If tool name already exists and overwrite=False
            TypeError: If function is not a coroutine function
            
        Example:
            async def my_tool(state: dict[str, Any]) -> dict[str, Any]:
                state['count'] += 1
                return state
            
            registry.register("increment", my_tool)
        """
        if not callable(func):
            raise TypeError(f"Tool '{name}' must be callable")
        
        # Check if it's an async function
        import inspect
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"Tool '{name}' must be an async function")
        
        if name in self._tools and not overwrite:
            raise ValueError(f"Tool '{name}' already registered. Use overwrite=True to replace.")
        
        self._tools[name] = func
        logger.info(f"Tool '{name}' registered successfully")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to remove
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        
        del self._tools[name]
        logger.info(f"Tool '{name}' unregistered")
    
    def get(self, name: str) -> ToolFunction:
        """
        Get a registered tool function.
        
        Args:
            name: Tool name
            
        Returns:
            ToolFunction: The tool function
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        
        return self._tools[name]
    
    def exists(self, name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            name: Tool name to check
            
        Returns:
            bool: True if tool exists
        """
        return name in self._tools
    
    def list_tools(self) -> list[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            list[str]: List of tool names
        """
        return list(self._tools.keys())
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("All tools cleared from registry")
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if tool exists using 'in' operator."""
        return name in self._tools


# Global tool registry instance
tool_registry = ToolRegistry()
