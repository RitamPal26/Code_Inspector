"""
Condition evaluation for workflow branching and loops.

Evaluates simple and complex conditions against workflow state
to determine control flow decisions.
"""

import logging
from typing import Any
from app.models.schemas import SimpleCondition, ComplexCondition
from app.core.state_manager import StateManager


logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates conditions for workflow control flow.
    
    Supports simple comparisons, collection operations, and
    complex logical expressions (AND, OR, NOT).
    """
    
    def __init__(self, state_manager: StateManager) -> None:
        """
        Initialize condition evaluator.
        
        Args:
            state_manager: State manager for accessing workflow state
        """
        self.state_manager = state_manager
    
    def evaluate(self, condition: SimpleCondition | ComplexCondition) -> bool:
        """
        Evaluate a condition against current state.
        
        Args:
            condition: Condition to evaluate
            
        Returns:
            bool: Evaluation result
            
        Raises:
            ValueError: If condition format is invalid
        """
        if isinstance(condition, SimpleCondition):
            return self._evaluate_simple(condition)
        elif isinstance(condition, ComplexCondition):
            return self._evaluate_complex(condition)
        else:
            raise ValueError(f"Unknown condition type: {type(condition)}")
    
    def _evaluate_simple(self, condition: SimpleCondition) -> bool:
        """
        Evaluate simple condition.
        
        Args:
            condition: Simple condition to evaluate
            
        Returns:
            bool: Evaluation result
        """
        # Get field value from state
        field_value = self.state_manager.get_field(condition.field)
        
        if field_value is None:
            logger.warning(f"Field '{condition.field}' not found in state, treating as None")
            field_value = None
        
        # Handle collection operations
        if condition.operator in ["length", "max", "min"]:
            return self._evaluate_collection_operation(
                field_value,
                condition.operator,
                condition.comparator,
                condition.value
            )
        
        # Handle contains operation
        if condition.operator == "contains":
            return self._evaluate_contains(field_value, condition.value)
        
        # Handle standard comparison
        return self._compare_values(field_value, condition.operator, condition.value)
    
    def _evaluate_complex(self, condition: ComplexCondition) -> bool:
        """
        Evaluate complex condition with logical operators.
        
        Args:
            condition: Complex condition to evaluate
            
        Returns:
            bool: Evaluation result
        """
        results = [self.evaluate(sub_cond) for sub_cond in condition.conditions]
        
        if condition.type == "AND":
            result = all(results)
        elif condition.type == "OR":
            result = any(results)
        elif condition.type == "NOT":
            result = not results[0]
        else:
            raise ValueError(f"Unknown logical operator: {condition.type}")
        
        logger.debug(f"Complex condition ({condition.type}) evaluated to {result}")
        return result
    
    def _evaluate_collection_operation(
        self,
        field_value: Any,
        operation: str,
        comparator: str | None,
        target_value: Any
    ) -> bool:
        """
        Evaluate collection operations (length, max, min).
        
        Args:
            field_value: Collection to evaluate
            operation: Operation type (length/max/min)
            comparator: Comparison operator
            target_value: Value to compare against
            
        Returns:
            bool: Evaluation result
        """
        if not isinstance(field_value, (list, dict, str)):
            logger.warning(f"Collection operation on non-collection type: {type(field_value)}")
            return False
        
        if operation == "length":
            actual_value = len(field_value)
        elif operation == "max":
            if not isinstance(field_value, list) or len(field_value) == 0:
                return False
            try:
                actual_value = max(field_value)
            except (TypeError, ValueError):
                return False
        elif operation == "min":
            if not isinstance(field_value, list) or len(field_value) == 0:
                return False
            try:
                actual_value = min(field_value)
            except (TypeError, ValueError):
                return False
        else:
            raise ValueError(f"Unknown collection operation: {operation}")
        
        if comparator is None:
            raise ValueError(f"Comparator required for {operation} operation")
        
        return self._compare_values(actual_value, comparator, target_value)
    
    def _evaluate_contains(self, field_value: Any, search_value: Any) -> bool:
        """
        Evaluate contains operation.
        
        Args:
            field_value: Collection to search in
            search_value: Value to search for
            
        Returns:
            bool: True if search_value in field_value
        """
        if field_value is None:
            return False
        
        if isinstance(field_value, (list, tuple, set)):
            return search_value in field_value
        elif isinstance(field_value, dict):
            return search_value in field_value.keys()
        elif isinstance(field_value, str):
            return str(search_value) in field_value
        else:
            return False
    
    def _compare_values(self, left: Any, operator: str, right: Any) -> bool:
        """
        Compare two values using operator.
        
        Args:
            left: Left operand
            operator: Comparison operator
            right: Right operand
            
        Returns:
            bool: Comparison result
        """
        try:
            if operator == "==":
                return left == right
            elif operator == "!=":
                return left != right
            elif operator == ">":
                return left > right
            elif operator == "<":
                return left < right
            elif operator == ">=":
                return left >= right
            elif operator == "<=":
                return left <= right
            else:
                raise ValueError(f"Unknown comparison operator: {operator}")
        except TypeError as e:
            logger.warning(f"Type error in comparison: {left} {operator} {right}: {e}")
            return False
    
    def __repr__(self) -> str:
        """String representation of condition evaluator."""
        return f"<ConditionEvaluator(state_fields={len(self.state_manager.current_state)})>"
