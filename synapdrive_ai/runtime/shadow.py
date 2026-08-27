from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class ShadowComparison:
    trusted_action: str
    shadow_action: str
    agreement: bool
    shadow_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ShadowController:
    """Evaluates an experimental policy without granting it actuation authority."""

    def __init__(self, policy: Callable[[Dict[str, Any]], tuple[str, Dict[str, Any]]]) -> None:
        self.policy = policy
        self.history: List[ShadowComparison] = []

    def evaluate(self, trusted_action: str, context: Dict[str, Any]) -> ShadowComparison:
        action, metadata = self.policy(dict(context))
        comparison = ShadowComparison(
            trusted_action=trusted_action,
            shadow_action=str(action),
            agreement=str(action) == str(trusted_action),
            shadow_metadata=dict(metadata),
        )
        self.history.append(comparison)
        return comparison
