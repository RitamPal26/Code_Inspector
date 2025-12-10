"""
Code Review Workflow Definition.

Defines the complete code review workflow with loop-based
quality improvement process.
"""

from app.models.schemas import (
    NodeDefinition,
    EdgeDefinition,
    GraphDefinition,
    SimpleCondition,
    ComplexCondition
)


def get_code_review_workflow() -> dict:
    """
    Get the code review workflow definition.
    
    Workflow Steps:
    1. extract_functions - Parse code and extract function metadata (runs once)
    2. improvement_loop (max 15 iterations):
       - check_complexity - Calculate cyclomatic complexity
       - detect_issues - Identify code quality issues
       - calculate_quality - Compute quality score (0-10)
       - DECISION: If quality_score >= 8, exit loop
       - suggest_improvements - Generate fix suggestions
       - apply_suggestions - Apply improvements (simulated)
       - Loop back to check_complexity
    
    Exit Condition: quality_score >= 8 OR iteration >= 15
    
    Returns:
        dict: Complete workflow definition for API
    """
    
    workflow_definition = {
        "name": "Code Review Mini-Agent",
        "description": "Automated code review with iterative quality improvement",
        "graph_definition": {
            "nodes": [
                # Step 1: Extract functions (runs once)
                {
                    "name": "extract_functions",
                    "type": "normal",
                    "tool_name": "extract_functions"
                },
                
                # Step 2: Improvement loop
                {
                    "name": "improvement_loop",
                    "type": "loop",
                    "nodes": [
                        "check_complexity",
                        "detect_issues",
                        "calculate_quality",
                        "suggest_improvements",
                        "apply_suggestions"
                    ],
                    "loop_condition": {
                        "field": "quality_score",
                        "operator": ">=",
                        "value": 8
                    },
                    "max_iterations": 15,
                    "on_max_reached": "fail"
                },
                
                # Individual loop nodes
                {
                    "name": "check_complexity",
                    "type": "normal",
                    "tool_name": "check_complexity"
                },
                {
                    "name": "detect_issues",
                    "type": "normal",
                    "tool_name": "detect_issues"
                },
                {
                    "name": "calculate_quality",
                    "type": "normal",
                    "tool_name": "calculate_quality"
                },
                {
                    "name": "suggest_improvements",
                    "type": "normal",
                    "tool_name": "suggest_improvements"
                },
                {
                    "name": "apply_suggestions",
                    "type": "normal",
                    "tool_name": "apply_suggestions"
                }
            ],
            
            "edges": [
                # Connect extract to loop
                {
                    "from_node": "extract_functions",
                    "to_node": "improvement_loop"
                }
            ],
            
            "initial_state_schema": {
                "code": "str",
                "functions": "list",
                "complexity_scores": "dict",
                "issues": "list",
                "quality_score": "float",
                "suggestions": "list",
                "improvements_applied": "int"
            }
        }
    }
    
    return workflow_definition


# Sample code for testing
SAMPLE_CODE_GOOD = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b

def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"
'''

SAMPLE_CODE_BAD = '''
def complex_function(a, b, c, d, e, f):
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        result = a + b + c + d + e + f
                    else:
                        result = a + b + c + d
                else:
                    result = a + b + c
            else:
                result = a + b
        else:
            result = a
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result += i * j * k
    return result

def another_long_function_without_docstring(param1, param2, param3, param4, param5, param6, param7):
    line1 = param1 + param2
    line2 = param3 + param4
    line3 = param5 + param6
    line4 = param7 + line1
    line5 = line2 + line3
    line6 = line4 + line5
    line7 = line1 * line2
    line8 = line3 * line4
    line9 = line5 * line6
    line10 = line7 + line8
    line11 = line9 + line10
    line12 = line11 * 2
    line13 = line12 + line1
    line14 = line13 + line2
    line15 = line14 + line3
    return line15
'''
