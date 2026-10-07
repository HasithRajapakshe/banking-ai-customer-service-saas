import os
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    os.environ["APP_ENV"] = "test"
    os.environ["TOOL_GATEWAY_BASE_URL"] = "http://localhost:8003"
    os.environ["TENANT_ID"] = "f498100f-80c4-467e-84ec-ebfe5470b442"
