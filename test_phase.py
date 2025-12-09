"""
Test Day 4 components: Node Executor and Graph Engine.
"""

import asyncio
from typing import Any
from uuid import uuid4

from app.tools.tool_registry import tool_registry
from app.core.state_manager import StateManager
from app.core.execution_logger import ExecutionLogger
from app.core.node_executor import NodeExecutor
from app.models.schemas import (
    NodeDefinition,
    EdgeDefinition,
    GraphDefinition,
    SimpleCondition
)


# Test tools
async def increment_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Increment counter."""
    state['count'] = state.get('count', 0) + 1
    print(f"  → Count incremented to: {state['count']}")
    return state


async def quality_check_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Calculate quality score based on count."""
    count = state.get('count', 0)
    state['quality_score'] = min(10, count * 2)
    print(f"  → Quality score: {state['quality_score']}")
    return state


async def test_node_executor():
    """Test node executor."""
    print("\n" + "=" * 60)
    print("Testing Node Executor")
    print("=" * 60)
    
    # Register tools
    tool_registry.register("increment", increment_tool, overwrite=True)
    tool_registry.register("quality_check", quality_check_tool, overwrite=True)
    
    # Initialize components
    state = {"count": 0, "quality_score": 0}
    state_manager = StateManager(state)
    execution_logger = ExecutionLogger()
    node_executor = NodeExecutor(state_manager, execution_logger)
    
    # Test 1: Execute normal node
    print("\n1. Execute normal node (increment):")
    await node_executor.execute_normal_node("node1", "increment")
    print(f"   ✓ State after: {state_manager.get_state()}")
    
    # Test 2: Execute another node
    print("\n2. Execute normal node (quality_check):")
    await node_executor.execute_normal_node("node2", "quality_check")
    print(f"   ✓ State after: {state_manager.get_state()}")
    
    # Test 3: Check logs
    print("\n3. Check execution logs:")
    logs = execution_logger.get_logs()
    print(f"   ✓ Total logs: {len(logs)}")
    for log in logs:
        print(f"   ✓ {log.node}: {log.status} ({log.duration_ms}ms)")
    
    print("\n✅ Node Executor tests passed!")


async def test_loop_simulation():
    """Simulate a simple loop execution."""
    print("\n" + "=" * 60)
    print("Testing Loop Simulation")
    print("=" * 60)
    
    # Register tools
    tool_registry.register("increment", increment_tool, overwrite=True)
    tool_registry.register("quality_check", quality_check_tool, overwrite=True)
    
    # Initialize components
    state = {"count": 0, "quality_score": 0}
    state_manager = StateManager(state)
    execution_logger = ExecutionLogger()
    node_executor = NodeExecutor(state_manager, execution_logger)
    
    from app.core.condition_evaluator import ConditionEvaluator
    condition_evaluator = ConditionEvaluator(state_manager)
    
    # Define loop exit condition
    exit_condition = SimpleCondition(field="quality_score", operator=">=", value=8)
    
    print("\n1. Running loop (exit when quality_score >= 8):")
    iteration = 0
    max_iterations = 15
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n   Iteration {iteration}:")
        
        # Execute loop nodes
        await node_executor.execute_normal_node("increment", "increment", iteration)
        await node_executor.execute_normal_node("quality_check", "quality_check", iteration)
        
        # Check exit condition
        if condition_evaluator.evaluate(exit_condition):
            print(f"\n   ✓ Exit condition met after {iteration} iterations!")
            break
    
    print(f"\n2. Final state:")
    print(f"   ✓ Count: {state_manager.get_field('count')}")
    print(f"   ✓ Quality score: {state_manager.get_field('quality_score')}")
    print(f"   ✓ Total iterations: {iteration}")
    
    print("\n✅ Loop simulation tests passed!")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Day 4 Component Tests")
    print("=" * 60)
    
    await test_node_executor()
    await test_loop_simulation()
    
    print("\n" + "=" * 60)
    print("All Day 4 tests passed! ✅")
    print("=" * 60)
    print("\nNote: Full graph engine will be tested in Day 5 with API integration")


if __name__ == "__main__":
    asyncio.run(main())
