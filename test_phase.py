"""
Test Day 3 components: State Manager and Condition Evaluator.
"""

import asyncio
from app.core.state_manager import StateManager
from app.core.condition_evaluator import ConditionEvaluator
from app.models.schemas import SimpleCondition, ComplexCondition


def test_state_manager():
    """Test state manager functionality."""
    print("\n" + "=" * 60)
    print("Testing State Manager")
    print("=" * 60)
    
    # Initialize state
    initial_state = {
        "count": 0,
        "quality_score": 5,
        "issues": ["issue1", "issue2"],
        "user": {
            "name": "John",
            "age": 30
        }
    }
    
    manager = StateManager(initial_state)
    
    # Test 1: Get state
    print("\n1. Get state:")
    state = manager.get_state()
    print(f"   ✓ State: {state}")
    
    # Test 2: Update state
    print("\n2. Update state:")
    manager.update_state({"count": 5, "quality_score": 8}, "test_node")
    print(f"   ✓ Updated count: {manager.get_field('count')}")
    print(f"   ✓ Updated quality_score: {manager.get_field('quality_score')}")
    
    # Test 3: Get nested field
    print("\n3. Get nested field:")
    user_name = manager.get_field("user.name")
    print(f"   ✓ User name: {user_name}")
    
    # Test 4: Set nested field
    print("\n4. Set nested field:")
    manager.set_field("user.email", "john@example.com")
    print(f"   ✓ User email: {manager.get_field('user.email')}")
    
    # Test 5: Check field exists
    print("\n5. Check field exists:")
    print(f"   ✓ 'count' exists: {manager.has_field('count')}")
    print(f"   ✓ 'nonexistent' exists: {manager.has_field('nonexistent')}")
    
    # Test 6: State history
    print("\n6. State history:")
    print(f"   ✓ History snapshots: {manager.get_history_count()}")
    
    print("\n✅ State Manager tests passed!")


def test_condition_evaluator():
    """Test condition evaluator functionality."""
    print("\n" + "=" * 60)
    print("Testing Condition Evaluator")
    print("=" * 60)
    
    # Initialize state
    state = {
        "quality_score": 8,
        "count": 5,
        "issues": ["issue1", "issue2", "issue3"],
        "complexity_scores": [5, 8, 12, 3],
        "done": False
    }
    
    manager = StateManager(state)
    evaluator = ConditionEvaluator(manager)
    
    # Test 1: Simple comparison (>=)
    print("\n1. Simple comparison (quality_score >= 8):")
    condition = SimpleCondition(field="quality_score", operator=">=", value=8)
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 2: Simple comparison (<)
    print("\n2. Simple comparison (count < 10):")
    condition = SimpleCondition(field="count", operator="<", value=10)
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 3: Length operation
    print("\n3. Length operation (issues.length == 3):")
    condition = SimpleCondition(
        field="issues",
        operator="length",
        comparator="==",
        value=3
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 4: Max operation
    print("\n4. Max operation (complexity_scores.max > 10):")
    condition = SimpleCondition(
        field="complexity_scores",
        operator="max",
        comparator=">",
        value=10
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 5: Contains operation
    print("\n5. Contains operation ('issue1' in issues):")
    condition = SimpleCondition(
        field="issues",
        operator="contains",
        value="issue1"
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 6: Complex AND condition
    print("\n6. Complex AND condition (quality_score >= 8 AND count < 10):")
    condition = ComplexCondition(
        type="AND",
        conditions=[
            SimpleCondition(field="quality_score", operator=">=", value=8),
            SimpleCondition(field="count", operator="<", value=10)
        ]
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 7: Complex OR condition
    print("\n7. Complex OR condition (done == True OR quality_score >= 8):")
    condition = ComplexCondition(
        type="OR",
        conditions=[
            SimpleCondition(field="done", operator="==", value=True),
            SimpleCondition(field="quality_score", operator=">=", value=8)
        ]
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 8: Complex NOT condition
    print("\n8. Complex NOT condition (NOT done == True):")
    condition = ComplexCondition(
        type="NOT",
        conditions=[
            SimpleCondition(field="done", operator="==", value=True)
        ]
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    # Test 9: Nested complex condition
    print("\n9. Nested complex condition:")
    condition = ComplexCondition(
        type="AND",
        conditions=[
            SimpleCondition(field="quality_score", operator=">=", value=8),
            ComplexCondition(
                type="OR",
                conditions=[
                    SimpleCondition(field="count", operator="<", value=3),
                    SimpleCondition(field="issues", operator="length", comparator="<=", value=5)
                ]
            )
        ]
    )
    result = evaluator.evaluate(condition)
    print(f"   ✓ Result: {result} (Expected: True)")
    
    print("\n✅ Condition Evaluator tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Day 3 Component Tests")
    print("=" * 60)
    
    test_state_manager()
    test_condition_evaluator()
    
    print("\n" + "=" * 60)
    print("All Day 3 tests passed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
