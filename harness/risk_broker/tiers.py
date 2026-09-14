"""Risk classification for hardware tool invocations.

The policy lives in policy/tool-tiers.yaml so it can be reviewed and edited
without touching code. First matching rule wins; anything unmatched falls
through to tier 3 (refuse and hand over to the human), because an unrecognised
command near real hardware should fail closed.

Structural refusals come *before* tiering
----------------------------------------
A command is first checked for shell metacharacters and parsed into an argv
list. This is not cosmetic. The original implementation classified only the
first shlex token while executing the whole string through `shell=True`, so
`kicad-cli sch erc b.kicad_sch; rm -rf ~/Documents` classified as T1 with an
allowed binary and would have run. Refusing metacharacters means one call is
exactly one command, which is what lets the policy rules anchor at `^` and
makes the binary allowlist meaningful.

Commands are executed with shell=False (see server.py), so these characters
would in any case be passed through as literal arguments rather than
interpreted. Refusing them keeps that from being a silent surprise, and keeps
the guarantee if anyone ever reintroduces a shell.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = Path(
    os.environ.get("RISK_BROKER_POLICY", _REPO_ROOT / "policy" / "tool-tiers.yaml")
)

# Characters that mean something to a shell. Order matters only for the message.
SHELL_METACHARACTERS = (";", "|", "&", "`", "$(", "${", ">", "<", "\n", "\r")


@dataclass
class Classification:
    tier: int
    rule: str
    reason: str
    see: str | None = None
    binary: str | None = None
    allowed_binary: bool = True
    argv: list[str] = field(default_factory=list)
    blocked: str | None = None

    @property
    def label(self) -> str:
        return {
            1: "T1 autonomous",
            2: "T2 confirm-first",
            3: "T3 advisory-only",
        }[self.tier]

    @property
    def runnable(self) -> bool:
        """True only if nothing structural stands in the way of executing."""
        return self.blocked is None and self.allowed_binary


def _refused(reason: str, blocked: str, argv: list[str] | None = None) -> Classification:
    """A structural refusal. Always tier 3: if we cannot parse it, we do not run it."""
    return Classification(
        tier=3,
        rule=blocked,
        reason=reason,
        argv=argv or [],
        allowed_binary=False,
        blocked=blocked,
    )


class Policy:
    def __init__(self, path: Path = POLICY_PATH):
        raw = yaml.safe_load(Path(path).read_text())
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

    @property
    def rule_names(self) -> list[str]:
        return [name for _, name, _, _, _ in self.rules]

    @staticmethod
    def _split(command: str) -> tuple[list[str], str | None]:
        """Parse into argv, or return the reason it cannot be parsed safely."""
        if not command or not command.strip():
            return [], "empty command"

        for meta in SHELL_METACHARACTERS:
            if meta in command:
                return [], (
                    f"command contains the shell metacharacter {meta!r}. "
                    "This broker executes one command at a time without a shell, "
                    "so pipes, redirects and chained commands are refused rather "
                    "than silently passed through as literal arguments. Split it "
                    "into separate calls, each of which is classified on its own."
                )

        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return [], f"cannot parse command ({exc}). Check the quoting."

        if not argv:
            return [], "empty command"
        return argv, None

    @staticmethod
    def _binary(argv: list[str]) -> str | None:
        """The executable, skipping any leading VAR=value environment prefixes."""
        for token in argv:
            if "=" in token and not token.startswith("-") and "/" not in token.split("=")[0]:
                continue
            return Path(token).name
        return None

    def classify(self, command: str) -> Classification:
        argv, parse_error = self._split(command)
        if parse_error:
            return _refused(parse_error, "unparseable", argv)

        binary = self._binary(argv)
        if binary is None:
            return _refused("no executable found in command", "unparseable", argv)

        allowed = binary in self.allowed
        normalized = " ".join(argv)

        for tier, name, pattern, reason, see in self.rules:
            if pattern.search(normalized):
                return Classification(
                    tier=tier,
                    rule=name,
                    reason=reason,
                    see=see,
                    binary=binary,
                    allowed_binary=allowed,
                    argv=argv,
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
            argv=argv,
        )
