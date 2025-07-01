"""Test configuration and fixtures."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_windows_specific_functions():
    """Mock Windows-incompatible functions for all tests."""
    # Only apply this mock on Windows or if getloadavg doesn't exist
    if not hasattr(os, 'getloadavg'):
        with patch('system_info_mcp.tools.os.getloadavg', return_value=(0.1, 0.1, 0.1), create=True):
            yield
    else:
        yield