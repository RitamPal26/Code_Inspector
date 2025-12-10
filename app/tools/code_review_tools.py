"""
Code review tools for workflow execution.

Implements tools for analyzing code quality, detecting issues,
and suggesting improvements in a rule-based manner.
"""

import re
import ast
from typing import Any
import logging


logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: EXTRACT FUNCTIONS
# ============================================================================

async def extract_functions(state: dict[str, Any]) -> dict[str, Any]:
    """
    Extract function definitions from code.
    
    Parses Python code and extracts all function definitions with
    metadata including name, line count, and parameters.
    
    Args:
        state: Must contain 'code' field with Python code string
        
    Returns:
        dict: Updated state with 'functions' list
        
    Example:
        Input: {"code": "def foo():\\n    pass"}
        Output: {"code": "...", "functions": [{"name": "foo", "lines": 2, ...}]}
    """
    code = state.get('code', '')
    
    if not code or not isinstance(code, str):
        logger.warning("No valid code found in state")
        state['functions'] = []
        return state
    
    functions = []
    
    try:
        # Parse code into AST
        tree = ast.parse(code)
        
        # Extract function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function source lines
                func_lines = []
                try:
                    source_lines = code.split('\n')
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        func_lines = source_lines[node.lineno - 1:node.end_lineno]
                except:
                    func_lines = []
                
                # Count actual code lines (excluding empty and comments)
                code_lines = [
                    line for line in func_lines
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                # Extract parameters
                params = [arg.arg for arg in node.args.args]
                
                # Check for docstring
                has_docstring = (
                    len(node.body) > 0 and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                
                functions.append({
                    'name': node.name,
                    'line_count': len(func_lines),
                    'code_line_count': len(code_lines),
                    'parameters': params,
                    'parameter_count': len(params),
                    'has_docstring': has_docstring,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                })
        
        logger.info(f"Extracted {len(functions)} functions from code")
        
    except SyntaxError as e:
        logger.error(f"Syntax error in code: {str(e)}")
        state['syntax_errors'] = [str(e)]
        state['functions'] = []
        return state
    except Exception as e:
        logger.error(f"Error extracting functions: {str(e)}")
        state['functions'] = []
        return state
    
    state['functions'] = functions
    return state


# ============================================================================
# TOOL 2: CHECK COMPLEXITY
# ============================================================================

async def check_complexity(state: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate cyclomatic complexity for each function.
    
    Uses a simplified complexity calculation based on control flow
    statements (if, for, while, try, except, with, and, or).
    
    Args:
        state: Must contain 'code' and 'functions' fields
        
    Returns:
        dict: Updated state with 'complexity_scores' dict
        
    Example:
        Output: {"complexity_scores": {"foo": 5, "bar": 3}}
    """
    code = state.get('code', '')
    functions = state.get('functions', [])
    
    if not code or not functions:
        logger.warning("No code or functions to analyze complexity")
        state['complexity_scores'] = {}
        return state
    
    complexity_scores = {}
    
    try:
        tree = ast.parse(code)
        
        for func_info in functions:
            func_name = func_info['name']
            complexity = 1  # Base complexity
            
            # Find the function node
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Count complexity-increasing constructs
                    for child in ast.walk(node):
                        # Control flow statements
                        if isinstance(child, (ast.If, ast.While, ast.For)):
                            complexity += 1
                        # Exception handling
                        elif isinstance(child, ast.ExceptHandler):
                            complexity += 1
                        # Boolean operators
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                        # Ternary expressions
                        elif isinstance(child, ast.IfExp):
                            complexity += 1
                        # List/dict/set comprehensions
                        elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                            complexity += 1
                    
                    break
            
            complexity_scores[func_name] = complexity
        
        logger.info(f"Calculated complexity for {len(complexity_scores)} functions")
        
    except Exception as e:
        logger.error(f"Error calculating complexity: {str(e)}")
        complexity_scores = {func['name']: 1 for func in functions}
    
    state['complexity_scores'] = complexity_scores
    return state


# ============================================================================
# TOOL 3: DETECT ISSUES
# ============================================================================

async def detect_issues(state: dict[str, Any]) -> dict[str, Any]:
    """
    Detect code quality issues.
    
    Identifies issues like:
    - Functions exceeding length limits
    - High complexity functions
    - Missing docstrings
    - Too many parameters
    - Deep nesting
    
    Args:
        state: Must contain 'functions' and 'complexity_scores'
        
    Returns:
        dict: Updated state with 'issues' list
    """
    functions = state.get('functions', [])
    complexity_scores = state.get('complexity_scores', {})
    improved_functions = set(state.get('improved_functions', []))
    
    issues = []
    
    # Thresholds
    MAX_LINES = 50
    MAX_COMPLEXITY = 10
    MAX_PARAMETERS = 5
    
    for func in functions:
        func_name = func['name']
        
        # Skip re-checking issues for functions that have been improved
        # (unless they still violate thresholds based on updated metrics)
        
        # Issue 1: Long function
        if func['code_line_count'] > MAX_LINES:
            issues.append({
                'type': 'long_function',
                'function': func_name,
                'severity': 'medium',
                'message': f"Function '{func_name}' has {func['code_line_count']} lines (max: {MAX_LINES})",
                'current_value': func['code_line_count'],
                'threshold': MAX_LINES
            })
        
        # Issue 2: High complexity
        complexity = complexity_scores.get(func_name, 1)
        if complexity > MAX_COMPLEXITY:
            issues.append({
                'type': 'high_complexity',
                'function': func_name,
                'severity': 'high',
                'message': f"Function '{func_name}' has complexity {complexity} (max: {MAX_COMPLEXITY})",
                'current_value': complexity,
                'threshold': MAX_COMPLEXITY
            })
        
        # Issue 3: Missing docstring (only check if not already improved)
        if not func['has_docstring'] and func_name not in improved_functions:
            issues.append({
                'type': 'missing_docstring',
                'function': func_name,
                'severity': 'low',
                'message': f"Function '{func_name}' is missing a docstring",
                'current_value': 0,
                'threshold': 1
            })
        
        # Issue 4: Too many parameters
        if func['parameter_count'] > MAX_PARAMETERS:
            issues.append({
                'type': 'too_many_parameters',
                'function': func_name,
                'severity': 'medium',
                'message': f"Function '{func_name}' has {func['parameter_count']} parameters (max: {MAX_PARAMETERS})",
                'current_value': func['parameter_count'],
                'threshold': MAX_PARAMETERS
            })
    
    logger.info(f"Detected {len(issues)} code quality issues")
    
    state['issues'] = issues
    return state


# ============================================================================
# TOOL 4: CALCULATE QUALITY
# ============================================================================

async def calculate_quality(state: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate overall code quality score (0-10).
    
    Scoring system:
    - Start with base score of 10
    - Deduct points based on issues and their severity
    - High severity: -2 points
    - Medium severity: -1 point
    - Low severity: -0.5 points
    
    Args:
        state: Must contain 'issues' list
        
    Returns:
        dict: Updated state with 'quality_score'
        
    Example:
        Output: {"quality_score": 7}
    """
    issues = state.get('issues', [])
    
    base_score = 10.0
    deductions = 0.0
    
    # Severity weights
    severity_weights = {
        'high': 2.0,
        'medium': 1.0,
        'low': 0.5
    }
    
    for issue in issues:
        severity = issue.get('severity', 'low')
        deductions += severity_weights.get(severity, 0.5)
    
    quality_score = max(0, base_score - deductions)
    
    logger.info(f"Calculated quality score: {quality_score}/10 ({len(issues)} issues)")
    
    state['quality_score'] = quality_score
    return state


# ============================================================================
# TOOL 5: SUGGEST IMPROVEMENTS
# ============================================================================

async def suggest_improvements(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate improvement suggestions based on detected issues.
    
    Creates actionable suggestions for fixing code quality issues.
    
    Args:
        state: Must contain 'issues' list
        
    Returns:
        dict: Updated state with 'suggestions' list
        
    Example:
        Output: {"suggestions": ["Break down large functions", ...]}
    """
    issues = state.get('issues', [])
    
    suggestions = []
    suggestion_templates = {
        'long_function': "Break down function '{function}' into smaller, focused functions",
        'high_complexity': "Simplify function '{function}' by extracting complex logic into separate functions",
        'missing_docstring': "Add a docstring to function '{function}' explaining its purpose, parameters, and return value",
        'too_many_parameters': "Reduce parameters in function '{function}' by grouping related parameters into objects"
    }
    
    # Track unique suggestions to avoid duplicates
    seen_suggestions = set()
    
    for issue in issues:
        issue_type = issue.get('type')
        func_name = issue.get('function')
        
        template = suggestion_templates.get(issue_type)
        if template:
            suggestion = template.format(function=func_name)
            
            if suggestion not in seen_suggestions:
                suggestions.append({
                    'type': issue_type,
                    'function': func_name,
                    'suggestion': suggestion,
                    'priority': issue.get('severity', 'low')
                })
                seen_suggestions.add(suggestion)
    
    logger.info(f"Generated {len(suggestions)} improvement suggestions")
    
    state['suggestions'] = suggestions
    return state


# ============================================================================
# TOOL 6: APPLY SUGGESTIONS (SIMULATED)
# ============================================================================

async def apply_suggestions(state: dict[str, Any]) -> dict[str, Any]:
    """
    Apply suggestions to improve code (simulated).
    
    This is a simplified simulation that marks functions as improved
    to demonstrate iterative quality enhancement without actual code refactoring.
    
    In a real implementation, this would use AST transformations or
    external refactoring tools.
    
    Args:
        state: Must contain 'suggestions' and 'issues'
        
    Returns:
        dict: Updated state with reduced issues and tracked improvements
    """
    suggestions = state.get('suggestions', [])
    issues = state.get('issues', [])
    functions = state.get('functions', [])
    
    if not suggestions:
        logger.info("No suggestions to apply")
        state['improvements_applied'] = state.get('improvements_applied', 0)
        return state
    
    # Track which functions have been "improved"
    improved_functions = state.get('improved_functions', set())
    if not isinstance(improved_functions, set):
        improved_functions = set(improved_functions) if improved_functions else set()
    
    improvements_count = 0
    remaining_issues = []
    
    # Track improvements by function and issue type
    improvements_by_function = {}
    
    for suggestion in suggestions:
        func_name = suggestion.get('function')
        issue_type = suggestion.get('type')
        
        if func_name not in improvements_by_function:
            improvements_by_function[func_name] = set()
        improvements_by_function[func_name].add(issue_type)
    
    # Filter out "fixed" issues
    for issue in issues:
        func_name = issue.get('function')
        issue_type = issue.get('type')
        
        # Check if this issue type has been addressed for this function
        if func_name in improvements_by_function and issue_type in improvements_by_function[func_name]:
            # Mark high and medium severity issues as fixed
            if issue['severity'] in ['high', 'medium']:
                improvements_count += 1
                improved_functions.add(func_name)
                logger.info(f"Fixed {issue_type} in {func_name}")
                continue  # Don't add to remaining issues
            # Low severity issues: reduce severity or fix after multiple iterations
            elif issue['severity'] == 'low':
                iteration = state.get('iteration_count', 0)
                if iteration >= 2:  # Fix low severity issues after 2 iterations
                    improvements_count += 1
                    improved_functions.add(func_name)
                    logger.info(f"Fixed {issue_type} in {func_name}")
                    continue
        
        # Keep unresolved issues
        remaining_issues.append(issue)
    
    # Update function metadata to reflect improvements
    for func in functions:
        if func['name'] in improved_functions:
            # Simulate code improvement by reducing metrics
            if 'code_line_count' in func:
                func['code_line_count'] = max(10, func['code_line_count'] - 5)
            if 'parameter_count' in func:
                func['parameter_count'] = max(2, func['parameter_count'] - 1)
            # Mark as having docstring after improvement
            func['has_docstring'] = True
    
    # Update complexity scores for improved functions
    complexity_scores = state.get('complexity_scores', {})
    for func_name in improved_functions:
        if func_name in complexity_scores:
            # Reduce complexity
            complexity_scores[func_name] = max(1, complexity_scores[func_name] - 2)
    
    # Update state
    state['functions'] = functions
    state['complexity_scores'] = complexity_scores
    state['issues'] = remaining_issues
    state['improved_functions'] = list(improved_functions)
    state['improvements_applied'] = state.get('improvements_applied', 0) + improvements_count
    
    logger.info(f"Applied {improvements_count} improvements, {len(remaining_issues)} issues remaining")
    
    return state