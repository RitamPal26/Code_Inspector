"""
State management for workflow execution.

Manages workflow state throughout execution including state updates,
history tracking, and validation.
"""

import logging
from typing import Any
from copy import deepcopy
from datetime import datetime


logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages workflow state across execution.
    
    Provides state storage, updates, history tracking, and retrieval
    functionality for workflow execution.
    
    Attributes:
        current_state: Current workflow state
        state_history: History of state snapshots
    """
    
    def __init__(self, initial_state: dict[str, Any]) -> None:
        """
        Initialize state manager with initial state.
        
        Args:
            initial_state: Starting state for workflow
        """
        self.current_state: dict[str, Any] = deepcopy(initial_state)
        self.state_history: list[dict[str, Any]] = []
        self._save_snapshot("initial")
        logger.info("State manager initialized")
    
    def get_state(self) -> dict[str, Any]:
        """
        Get current workflow state.
        
        Returns a deep copy to prevent external modifications.
        
        Returns:
            dict[str, Any]: Current state
        """
        return deepcopy(self.current_state)
    
    def update_state(self, updates: dict[str, Any], node_name: str | None = None) -> dict[str, Any]:
        """
        Update current state with new values.
        
        Merges updates into current state and saves snapshot.
        
        Args:
            updates: Dictionary of updates to apply
            node_name: Name of node making the update (for tracking)
            
        Returns:
            dict[str, Any]: Updated state
        """
        self.current_state.update(updates)
        self._save_snapshot(node_name or "update")
        
        logger.debug(f"State updated by {node_name or 'unknown'}: {list(updates.keys())}")
        
        return self.get_state()
    
    def set_state(self, new_state: dict[str, Any], node_name: str | None = None) -> dict[str, Any]:
        """
        Replace entire state with new state.
        
        Args:
            new_state: New state to set
            node_name: Name of node setting the state
            
        Returns:
            dict[str, Any]: New state
        """
        self.current_state = deepcopy(new_state)
        self._save_snapshot(node_name or "set")
        
        logger.debug(f"State replaced by {node_name or 'unknown'}")
        
        return self.get_state()
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get value from state using dot notation.
        
        Supports nested field access like "user.profile.name".
        
        Args:
            field_path: Dot-notation path to field
            default: Default value if field not found
            
        Returns:
            Any: Field value or default
            
        Example:
            state = {"user": {"name": "John", "age": 30}}
            manager.get_field("user.name")  # Returns "John"
            manager.get_field("user.email", "N/A")  # Returns "N/A"
        """
        try:
            value = self.current_state
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value[key]
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    return default
            return value
        except (KeyError, IndexError, TypeError):
            return default
    
    def set_field(self, field_path: str, value: Any) -> None:
        """
        Set value in state using dot notation.
        
        Creates nested dictionaries as needed.
        
        Args:
            field_path: Dot-notation path to field
            value: Value to set
            
        Example:
            manager.set_field("user.name", "John")
            manager.set_field("settings.theme.dark", True)
        """
        keys = field_path.split('.')
        current = self.current_state
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        logger.debug(f"Field '{field_path}' set to {value}")
    
    def has_field(self, field_path: str) -> bool:
        """
        Check if field exists in state.
        
        Args:
            field_path: Dot-notation path to field
            
        Returns:
            bool: True if field exists
        """
        try:
            value = self.current_state
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return False
            return True
        except (KeyError, IndexError, TypeError):
            return False
    
    def get_history(self) -> list[dict[str, Any]]:
        """
        Get state history snapshots.
        
        Returns:
            list[dict[str, Any]]: List of state snapshots
        """
        return deepcopy(self.state_history)
    
    def get_history_count(self) -> int:
        """
        Get number of state snapshots.
        
        Returns:
            int: Number of snapshots
        """
        return len(self.state_history)
    
    def _save_snapshot(self, label: str) -> None:
        """
        Save current state snapshot.
        
        Args:
            label: Label for this snapshot
        """
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "label": label,
            "state": deepcopy(self.current_state)
        }
        self.state_history.append(snapshot)
    
    def __repr__(self) -> str:
        """String representation of state manager."""
        return f"<StateManager(fields={len(self.current_state)}, snapshots={len(self.state_history)})>"
