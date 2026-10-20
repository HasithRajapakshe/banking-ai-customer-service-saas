import os
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    os.environ["APP_ENV"] = "test"
    os.environ["SYNTHETIC_BANK_BASE_URL"] = "http://localhost:8000"
    os.environ["SYNTHETIC_BANK_API_KEY"] = "test_key"
    os.environ["INTERNAL_API_KEY"] = "test_key"
