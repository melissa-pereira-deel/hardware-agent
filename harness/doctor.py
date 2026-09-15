#!/usr/bin/env python3
"""Report which allowlisted tools are actually runnable.

policy/tool-tiers.yaml names the binaries the risk broker will execute. It says
nothing about whether they exist. This closes that gap: before this existed, 28
of 34 allowlisted tools were not installed, so the skills instructed the agent
to run commands that could not run.

    python3 harness/doctor.py
    python3 harness/doctor.py --missing   # only what is absent, with install lines
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

# How to get each one on macOS. See TOOLS.md for what they do and why.
INSTALL = {
    "kicad-cli": "brew install --cask kicad            # 1.3 GB",
    "kikit": "uv tool install kikit",
    "kibot": "uv tool install kibot",
    "pcbdraw": "uv tool install pcbdraw",
    "kicost": "uv tool install kicost",
    "ngspice": "brew install ngspice",
    "gerbv": "brew install gerbv                      # deprecated in brew, EOL gtk+",
    "openscad": "brew install --cask openscad",
    "freecad": "brew install --cask freecad",
    "admesh": "brew install admesh",
    "arduino-cli": "brew install arduino-cli",
    "pio": "uv tool install platformio",
    "platformio": "uv tool install platformio",
    "idf.py": "see Espressif ESP-IDF install guide (get_idf)",
    "esptool": "uv tool install esptool",
    "espefuse": "uv tool install esptool               # ships with esptool",
    "esphome": "uv tool install esphome",
    "wokwi-cli": "curl -L https://wokwi.com/ci/install.sh | sh",
    "openocd": "brew install open-ocd",
    "probe-rs": "curl -LsSf https://probe.rs/install.sh | sh   # not in brew",
    "pyocd": "uv tool install pyocd",
    "picotool": "brew install picotool",
    "avrdude": "brew install avrdude",
    "orcaslicer": "brew install --cask orcaslicer",
    "prusa-slicer-console": "brew install --cask prusaslicer",
    "CuraEngine": "brew install cura-engine",
    "sigrok-cli": "brew install sigrok-cli",
    "mosquitto_pub": "brew install mosquitto",
    "mosquitto_sub": "brew install mosquitto",
    "gpioget": "Linux only (libgpiod). Belongs on the Pi, not the Mac.",
    "gpioset": "Linux only (libgpiod). Belongs on the Pi, not the Mac.",
    "i2cdetect": "Linux only (i2c-tools). Belongs on the Pi, not the Mac.",
    "i2cget": "Linux only (i2c-tools). Belongs on the Pi, not the Mac.",
    "i2cset": "Linux only (i2c-tools). Belongs on the Pi, not the Mac.",
    "pandoc": "brew install pandoc",
    "trafilatura": "uv tool install trafilatura",
    "docling": "uv tool install docling",
    "crwl": "uv tool install crawl4ai",
    "mlx_vlm": "uv pip install mlx-vlm",
    "ollama": "brew install ollama",
    "ripgrep": "brew install ripgrep                   # binary is `rg`",
}

# Named in the allowlist but not a real executable, or intentionally absent.
NOT_A_BINARY = {"ripgrep", "python", "python3", "git", "curl", "rg", "wget", "httpx"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--missing", action="store_true")
    args = ap.parse_args()

    raw = yaml.safe_load((REPO / "policy" / "tool-tiers.yaml").read_text())
    allowed = list(raw["binaries_allowed"])

    present = [b for b in allowed if shutil.which(b)]
    absent = [b for b in allowed if not shutil.which(b)]

    if not args.missing:
        print(f"allowlisted: {len(allowed)}   runnable: {len(present)}   missing: {len(absent)}\n")
        print("runnable:")
        for b in present:
            print(f"  ok   {b}")
        print()

    print("missing:")
    for b in absent:
        hint = INSTALL.get(b, "")
        note = "  (core toolchain, not a standalone binary)" if b in NOT_A_BINARY else ""
        print(f"  --   {b:<22} {hint}{note}")

    print(
        "\nA missing tool is not an error - the broker returns "
        "'executable not found' cleanly. It does mean any skill instruction "
        "naming it cannot be followed. See TOOLS.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
