import pytest

from app.factory import (
    build_provider,
    get_banking_provider,
    reset_provider,
)
from app.providers.synthetic_bank import SyntheticBankAdapter


class TestFactory:

    def setup_method(self):
        reset_provider()

    def teardown_method(self):
        reset_provider()

    def test_synthetic_provider_selected(self):
        provider = build_provider("synthetic")
        assert isinstance(provider, SyntheticBankAdapter)

    def test_unknown_provider_rejected(self):
        with pytest.raises(RuntimeError, match="Unsupported"):
            build_provider("unknown_bank")

    def test_provider_cached(self):
        first = get_banking_provider()
        second = get_banking_provider()

        assert first is second

    def test_provider_type(self):
        provider = get_banking_provider()
        assert isinstance(provider, SyntheticBankAdapter)

    def test_reset_clears_cache(self):
        first = get_banking_provider()
        reset_provider()
        second = get_banking_provider()

        assert first is not second
