from __future__ import annotations

import pytest

from synapdrive_ai.pipeline import SynapDrivePipeline


@pytest.fixture()
def pipeline() -> SynapDrivePipeline:
    """
    Shared pipeline fixture for fast, deterministic tests.
    """
    return SynapDrivePipeline(simulate_delay=False)
