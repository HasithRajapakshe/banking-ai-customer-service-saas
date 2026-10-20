import logging
import sys


def setup_logging() -> None:
    """
    Configure structured logging for the Banking Adapter.

    Logs include correlation_id-friendly formatting.
    Sensitive data (API keys, credentials, card numbers)
    must NEVER be passed to the logger.
    """

    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s | %(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Reduce noise from third-party libraries.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
