import re


class SecurityService:
    """Phase-6 pre-agent security screening.

    This is intentionally deterministic. A dedicated Guardrail/Security
    Service can replace/extend it later without changing the graph boundary.
    """

    _blocked_patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"reveal\s+(the\s+)?system\s+prompt",
        r"show\s+(me\s+)?(database|db)\s+(password|credentials)",
        r"bypass\s+(authentication|authorization|security)",
        r"give\s+me\s+your\s+(api\s+key|secret)",
    ]

    def check(self, message: str) -> tuple[bool, str | None]:
        normalized = " ".join(message.lower().split())
        for pattern in self._blocked_patterns:
            if re.search(pattern, normalized):
                return False, "The request violates the agent security policy."
        return True, None


security_service = SecurityService()
