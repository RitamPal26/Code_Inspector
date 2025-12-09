"""
Quick test for Day 2 components.
"""

import asyncio
from app.tools.tool_registry import tool_registry
from app.core.execution_logger import ExecutionLogger
from app.models.schemas import (
    SimpleCondition,
    ComplexCondition,
    NodeDefinition,
    EdgeDefinition,
    GraphDefinition
)


# Test tool function
async def test_tool(state: dict) -> dict:
    """Test tool that increments a counter."""
    state['count'] = state.get('count', 0) + 1
    return state


async def main():
    """Run tests."""
    print("=" * 60)
    print("Day 2 Component Tests")
    print("=" * 60)
    
    # Test 1: Tool Registry
    print("\n1. Testing Tool Registry...")
    tool_registry.register("test_tool", test_tool)
    print(f"   ✓ Registered tools: {tool_registry.list_tools()}")
    print(f"   ✓ Tool exists: {tool_registry.exists('test_tool')}")
    
    # Test 2: Execution Logger
    print("\n2. Testing Execution Logger...")
    logger = ExecutionLogger()
    logger.log_node_execution("node1", "success", message="Test successful")
    logger.log_node_execution("node2", "failed", iteration=1, message="Test error")
    print(f"   ✓ Logged {len(logger.get_logs())} entries")
    print(f"   ✓ First log: {logger.get_logs()[0].node} - {logger.get_logs()[0].status}")
    
    # Test 3: Simple Condition
    print("\n3. Testing Simple Condition...")
    condition = SimpleCondition(field="score", operator=">=", value=5)
    print(f"   ✓ Created condition: {condition.field} {condition.operator} {condition.value}")
    
    # Test 4: Complex Condition
    print("\n4. Testing Complex Condition...")
    complex_cond = ComplexCondition(
        type="AND",
        conditions=[
            SimpleCondition(field="score", operator=">=", value=5),
            SimpleCondition(field="count", operator="<", value=10)
        ]
    )
    print(f"   ✓ Created complex condition with {len(complex_cond.conditions)} subconditions")
    
    # Test 5: Node Definition
    print("\n5. Testing Node Definition...")
    node = NodeDefinition(name="test_node", type="normal", tool_name="test_tool")
    print(f"   ✓ Created node: {node.name} (type: {node.type})")
    
    # Test 6: Loop Node Definition
    print("\n6. Testing Loop Node...")
    loop_node = NodeDefinition(
        name="loop_test",
        type="loop",
        nodes=["node1", "node2"],
        loop_condition=SimpleCondition(field="done", operator="==", value=True),
        max_iterations=15
    )
    print(f"   ✓ Created loop node with {len(loop_node.nodes)} child nodes")
    
    # Test 7: Graph Definition
    print("\n7. Testing Graph Definition...")
    graph = GraphDefinition(
        nodes=[
            NodeDefinition(name="start", type="normal", tool_name="test_tool"),
            NodeDefinition(name="end", type="normal", tool_name="test_tool")
        ],
        edges=[
            EdgeDefinition(from_node="start", to_node="end")
        ],
        initial_state_schema={"count": "int", "done": "bool"}
    )
    print(f"   ✓ Created graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    print("\n" + "=" * 60)
    print("All Day 2 tests passed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
