# synapdrive_ai/tests/conftest.py

import pytest
from synapdrive_ai.pipeline import SynapDrivePipeline


@pytest.fixture()
def pipeline():
    """
    Shared pipeline fixture for fast, deterministic tests.
    """
    return SynapDrivePipeline()
