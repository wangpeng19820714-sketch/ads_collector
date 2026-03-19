from __future__ import annotations

from parser.parser import ParsedAd


class HookClassifier:
    """Rule-based hook classifier for V1."""

    def classify(self, ad: ParsedAd) -> str:
        hook = ad.hook.lower()
        if any(keyword in hook for keyword in ("free", "gift", "bonus", "reward")):
            return "incentive"
        if any(keyword in hook for keyword in ("before", "after", "transform", "upgrade")):
            return "transformation"
        if any(keyword in hook for keyword in ("storm", "danger", "save", "survive")):
            return "urgency"
        return "generic"

    def is_winner_candidate(self, ad: ParsedAd, min_days: int = 7) -> bool:
        if ad.first_seen is None or ad.last_seen is None:
            return False
        return (ad.last_seen - ad.first_seen).days >= min_days

