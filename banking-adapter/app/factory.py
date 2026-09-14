from app.core.config import settings
from app.providers.base import BankingProvider
from app.providers.synthetic_bank import SyntheticBankAdapter


_provider: BankingProvider | None = None


def build_provider(provider_name: str) -> BankingProvider:
    """
    Create a new BankingProvider instance for the
    given provider name.
    """

    if provider_name == "synthetic":
        return SyntheticBankAdapter()

    raise RuntimeError(
        f"Unsupported banking provider: {provider_name!r}. "
        f"Supported providers: synthetic"
    )


def get_banking_provider() -> BankingProvider:
    """
    Return the cached BankingProvider singleton.
    Creates it on first call.
    """

    global _provider

    if _provider is None:
        _provider = build_provider(
            settings.banking_provider.lower(),
        )

    return _provider


def reset_provider() -> None:
    """
    Reset the cached provider.
    Used primarily in tests.
    """

    global _provider
    _provider = None