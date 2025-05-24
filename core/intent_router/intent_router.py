# /core/intent_router/intent_router.py

"""
Intent Router Module

This module receives structured intents from the IntentParser and routes them to
the appropriate downstream modules (AGI planner, real-time executor, etc).
"""

from typing import Dict, Optional
from core.planning.agi_planner import AGIPlanner
from core.execution.executor_bridge import ExecutorBridge

class IntentRouter:
    """
    Routes structured intents to the correct subsystem:
    - AGIPlanner: for high-level planning and reasoning
    - ExecutorBridge: for direct low-latency execution
    """

    def __init__(self, use_realtime: bool = False):
        self.use_realtime = use_realtime
        self.planner = AGIPlanner()
        self.executor = ExecutorBridge()

    def route(self, intent: Dict) -> Optional[str]:
        """
        Routes an intent to the proper module.

        Parameters:
            intent (Dict): Parsed intent with 'intent' and 'params' fields

        Returns:
            str: Response or status
        """
        if not intent or "intent" not in intent:
            return "Invalid intent format"

        intent_type = intent["intent"]
        params = intent.get("params", {})

        if self.use_realtime or intent_type in ["move", "stop", "pick_up", "drop"]:
            return self.executor.execute(intent_type, params)
        else:
            return self.planner.plan(intent_type, params)

# Example usage
if __name__ == "__main__":
    from core.intent_router.intent_parser import IntentParser

    parser = IntentParser()
    router = IntentRouter()

    inputs = ["move forward", "switch mode to autonomous", "pick up"]
    for text in inputs:
        parsed = parser.parse(text)
        result = router.route(parsed)
        print(f"Input: {text} → Output: {result}")
