import pytest

from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class TestToolRegistry:
    def test_register_and_lookup(self):
        registry = ToolRegistry()
        tools = self._get_all_tools()

        for tool in tools:
            registry.register(tool)

        assert registry.count() == len(tools)

    def test_duplicate_registration_fails(self):
        from app.tools.account_tools import GetAccountBalanceTool

        registry = ToolRegistry()
        registry.register(GetAccountBalanceTool())

        with pytest.raises(RuntimeError, match="Duplicate"):
            registry.register(GetAccountBalanceTool())

    def test_lookup_unknown_tool(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent.tool") is None

    def test_all_returns_list(self):
        registry = ToolRegistry()
        assert registry.all() == []

        from app.tools.account_tools import GetAccountBalanceTool

        registry.register(GetAccountBalanceTool())
        result = registry.all()
        assert len(result) == 1
        assert result[0].name == "account.get_balance"

    def test_default_tools_count(self):
        """Verify all 25 tools are registered."""
        from app.tools.registry import _DEFAULT_TOOLS

        assert len(_DEFAULT_TOOLS) == 25

    def test_tool_listing_returns_metadata(self):
        from app.tools.account_tools import GetAccountBalanceTool

        registry = ToolRegistry()
        tool = GetAccountBalanceTool()
        registry.register(tool)

        t = registry.get("account.get_balance")
        assert t is not None
        assert t.name == "account.get_balance"
        assert t.permission == "account.balance.read"
        assert t.risk_level.value == "LOW"

    @staticmethod
    def _get_all_tools():
        from app.tools.registry import _DEFAULT_TOOLS

        return [cls() for cls in _DEFAULT_TOOLS]
