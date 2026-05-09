"""Shared pytest fixtures."""
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_runner():
    """Returns a runner stub that records calls and returns canned responses.

    Tests configure responses via mock_runner.return_value or side_effect.
    Default returns success with empty data.
    """
    runner = MagicMock()
    runner.return_value = {"success": True, "code": 200, "data": {}, "message": "OK"}
    return runner
