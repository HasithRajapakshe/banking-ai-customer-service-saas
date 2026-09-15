from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def requires_confirmation(
    risk_level: RiskLevel,
) -> bool:
    return risk_level in {
        RiskLevel.HIGH,
        RiskLevel.CRITICAL,
    }