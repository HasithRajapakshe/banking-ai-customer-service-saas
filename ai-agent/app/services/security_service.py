import re


class SecurityService:
    """Pre-agent screening for prompt injection and abuse.

    Deterministic by design: it runs before any model sees the message, so a
    blocked request never reaches the LLM or a tool. A dedicated Guardrail
    service can replace it later without changing the graph boundary.
    """

    _blocked_patterns = [
        # Override the instructions
        r"\b(ignore|disregard|forget|override|skip)\b.{0,30}\b(previous|prior|above|earlier|all|your|the|system)\b.{0,20}\b(instructions?|rules?|prompts?|guidelines|polic(y|ies))\b",
        r"\bnew\s+instructions?\s*:",
        # Extract the prompt or configuration
        r"\b(reveal|show|print|repeat|display|output|tell\s+me|what\s+(is|are))\b.{0,30}\b(system|hidden|initial|original|developer)\s+(prompt|instructions?|message|rules)\b",
        r"\b(reveal|show|print|repeat)\b.{0,15}\byour\s+(prompt|instructions?|rules)\b",
        r"\bshow\s+(me\s+)?(the\s+)?(database|db)\s+(password|credentials)",
        r"\bgive\s+me\s+(your|the)\s+(api\s+key|secret|token|password)",
        # Role-play / jailbreak
        r"\byou\s+are\s+now\b.{0,30}\b(dan|unrestricted|unfiltered|jailbroken|developer\s+mode|admin|root|system)\b",
        r"\b(developer|god|dan|jailbreak)\s+mode\b",
        r"\b(pretend|act|behave)\s+(to\s+be|as|like)\b.{0,20}\b(admin|administrator|system|root|bank\s+employee|support\s+agent|developer)\b",
        # Bypass controls
        r"\bbypass\b.{0,20}\b(authentication|authori[sz]ation|security|confirmation|verification|otp|limits?)\b",
        r"\b(without|skip|skipping)\b.{0,15}\b(confirmation|confirming|verification)\b",
        r"\b(confirm|approve)\s+(it|this|the\s+\w+)\s+(yourself|for\s+me\s+automatically|automatically)\b",
        r"\b(set|mark)\b.{0,20}\bconfirmed\s*(=|to|as)\s*(true|yes)\b",
        r"\bconfirmed\s*[:=]\s*true\b",
        r"\bchallenge_code\b",
        # Act for someone else
        r"\b(customer_id|tenant_id|user_id)\s*[:=]",
        r"\b(another|other|different|someone\s+else'?s)\s+(customer|user|person)'?s?\b.{0,30}\b(account|card|balance|transactions?|loan|payment)",
        r"\b(all|every)\s+(customers?|users?)'?\s+(accounts?|cards?|balances?|data|details)\b",
        # Markup pretending to be system/tool messages
        r"<\s*/?\s*(system|assistant|tool)\s*>",
        r"^\s*#{2,}\s*(system|instructions?)\b",
        r"\[\s*(system|inst)\s*\]",
        # Sinhala-English (Singlish) variants of "ignore/forget the previous instructions"
        r"\b(kalin|issara|parana)\b.{0,20}\b(instructions?|rules?|upades)\b.{0,20}\b(amathaka|ignore|nathuwa|epa)\b",
        r"\b(system\s+prompt|instructions?)\b.{0,20}\b(pennanna|kiyanna|denna)\b",
    ]
    _compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _blocked_patterns]

    def check(self, message: str) -> tuple[bool, str | None]:
        normalized = " ".join(message.split())
        for pattern in self._compiled:
            if pattern.search(normalized) or pattern.search(message):
                return False, "The request violates the agent security policy."
        return True, None


security_service = SecurityService()
