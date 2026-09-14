import pytest

from app.core.errors import (
    BankingAdapterError,
    map_provider_error,
)


class TestMapProviderError:

    def test_404_customer(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Customer not found",
                }
            },
            correlation_id="corr-1",
        )

        assert isinstance(err, BankingAdapterError)
        assert err.status_code == 404
        assert err.code == "CUSTOMER_NOT_FOUND"
        assert err.correlation_id == "corr-1"

    def test_404_account(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Account not found",
                }
            },
            correlation_id="corr-2",
        )

        assert err.code == "ACCOUNT_NOT_FOUND"

    def test_404_card(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Card not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "CARD_NOT_FOUND"

    def test_404_payment(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Payment not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "PAYMENT_NOT_FOUND"

    def test_404_beneficiary(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Beneficiary not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "BENEFICIARY_NOT_FOUND"

    def test_404_loan(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Loan not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "LOAN_NOT_FOUND"

    def test_404_complaint(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Complaint not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "COMPLAINT_NOT_FOUND"

    def test_404_unknown_resource(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "message": "Something not found",
                }
            },
            correlation_id=None,
        )

        assert err.code == "RESOURCE_NOT_FOUND"

    def test_503(self):
        err = map_provider_error(
            status_code=503,
            payload=None,
            correlation_id="corr-3",
        )

        assert err.code == "PROVIDER_UNAVAILABLE"
        assert err.status_code == 503

    def test_504(self):
        err = map_provider_error(
            status_code=504,
            payload=None,
            correlation_id=None,
        )

        assert err.code == "PROVIDER_TIMEOUT"

    def test_400_invalid_request(self):
        err = map_provider_error(
            status_code=400,
            payload={
                "error": {
                    "message": "Bad request",
                }
            },
            correlation_id=None,
        )

        assert err.code == "INVALID_REQUEST"

    def test_preserves_provider_code(self):
        err = map_provider_error(
            status_code=404,
            payload={
                "error": {
                    "code": "CUSTOM_CODE",
                    "message": "Custom error",
                }
            },
            correlation_id=None,
        )

        assert err.code == "CUSTOM_CODE"

    def test_preserves_correlation_from_payload(self):
        err = map_provider_error(
            status_code=500,
            payload={
                "error": {
                    "message": "Error",
                    "correlation_id": "from-provider",
                }
            },
            correlation_id="from-request",
        )

        assert err.correlation_id == "from-provider"
