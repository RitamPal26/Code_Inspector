"""
Tools package initialization.

Registers all tools on import.
"""

from app.tools.tool_registry import tool_registry
from app.tools.code_review_tools import (
    extract_functions,
    check_complexity,
    detect_issues,
    calculate_quality,
    suggest_improvements,
    apply_suggestions
)
from typing import Any


# ============================================================================
# SIMPLE TEST TOOLS (for basic testing)
# ============================================================================

async def increment(state: dict[str, Any]) -> dict[str, Any]:
    """Increment counter in state."""
    state['count'] = state.get('count', 0) + 1
    return state


async def quality_check(state: dict[str, Any]) -> dict[str, Any]:
    """Calculate quality score based on count."""
    count = state.get('count', 0)
    state['quality_score'] = min(10, count * 2)
    return state


# ============================================================================
# REGISTER ALL TOOLS
# ============================================================================

# Register simple test tools
tool_registry.register("increment", increment, overwrite=True)
tool_registry.register("quality_check", quality_check, overwrite=True)

# Register code review tools
tool_registry.register("extract_functions", extract_functions, overwrite=True)
tool_registry.register("check_complexity", check_complexity, overwrite=True)
tool_registry.register("detect_issues", detect_issues, overwrite=True)
tool_registry.register("calculate_quality", calculate_quality, overwrite=True)
tool_registry.register("suggest_improvements", suggest_improvements, overwrite=True)
tool_registry.register("apply_suggestions", apply_suggestions, overwrite=True)
