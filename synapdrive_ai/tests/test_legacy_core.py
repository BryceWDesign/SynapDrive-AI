from __future__ import annotations

from core.intent_router.intent_parser import IntentParser
from core.intent_router.intent_router import IntentRouter


def test_legacy_core_router_example_remains_importable() -> None:
    parser = IntentParser()
    router = IntentRouter(use_realtime=True)

    parsed = parser.parse("move forward")
    assert parsed is not None
    result = router.route(parsed)

    assert result == "Executed simulated move: forward"
