"""Risk classification for hardware tool invocations.

The policy lives in policy/tool-tiers.yaml so it can be reviewed and edited
without touching code. First matching rule wins; anything unmatched falls
through to tier 3 (refuse and hand over to the human), because an unrecognised
command near real hardware should fail closed.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path

import yaml

POLICY_PATH = Path(__file__).resolve().parents[2] / "policy" / "tool-tiers.yaml"


@dataclass
class Classification:
    tier: int
    rule: str
    reason: str
    see: str | None = None
    binary: str | None = None
    allowed_binary: bool = True

    @property
    def label(self) -> str:
        return {
            1: "T1 autonomous",
            2: "T2 confirm-first",
            3: "T3 advisory-only",
        }[self.tier]


class Policy:
    def __init__(self, path: Path = POLICY_PATH):
        raw = yaml.safe_load(path.read_text())
        self.allowed = set(raw.get("binaries_allowed", []))
        self.default_tier = int(raw.get("default_tier", 3))
        self.rules = [
            (
                int(r["tier"]),
                r["name"],
                re.compile(r["match"], re.IGNORECASE),
                " ".join(r["reason"].split()),
                r.get("see"),
            )
            for r in raw["rules"]
        ]

    @staticmethod
    def _binary(command: str) -> str | None:
        try:
            parts = shlex.split(command)
        except ValueError:
            return None
        for part in parts:
            # skip env assignments like FOO=bar
            if "=" in part and not part.startswith("-"):
                continue
            return Path(part).name
        return None

    def classify(self, command: str) -> Classification:
        binary = self._binary(command)
        allowed = binary in self.allowed if binary else False

        for tier, name, pattern, reason, see in self.rules:
            if pattern.search(command):
                return Classification(
                    tier=tier,
                    rule=name,
                    reason=reason,
                    see=see,
                    binary=binary,
                    allowed_binary=allowed,
                )

        return Classification(
            tier=self.default_tier,
            rule="unmatched",
            reason=(
                "No policy rule matched this command. Unrecognised commands near "
                "real hardware fail closed: review it, then run it yourself or add "
                "a rule to policy/tool-tiers.yaml."
            ),
            binary=binary,
            allowed_binary=allowed,
        )
