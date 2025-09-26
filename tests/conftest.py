"""Test configuration and fixtures"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide test data directory path"""
    return "tests/data"


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset global caches before each test"""
    import app.main
    app.main._data_cache = None
    app.main._validation_cache = None
    yield
    app.main._data_cache = None
    app.main._validation_cache = None