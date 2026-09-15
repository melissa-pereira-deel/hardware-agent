# Tools

Open-source tools this agent can drive, what tier each falls in, and how to get
them. Scoped to the stack this repo is built for — ESP32 firmware, KiCad PCBs,
LED and power work, 3D-printed enclosures, sourcing. Not a survey of the
hardware ecosystem; CNC, laser, FPGA and RF tooling are deliberately absent.

**Single source of truth.** The skills point here rather than restating install
instructions. The previous arrangement kept tool names in three places — the
allowlist, the tier rules, and each skill's Tools section — and they drifted:
`grep`, `gpioset`, `i2cdetect` and `mosquitto_pub` all had tier rules while the
allowlist refused them, making those rules unreachable.
`harness/tests/test_tiers.py::test_rules_and_allowlist_do_not_drift` now fails
if that recurs.

Run `just doctor` for what is installed on *your* machine right now.

Licences are as published by Homebrew or PyPI, checked **2026-09-14**. Where a
source did not state one it is marked unverified rather than guessed.

---

## Being allowlisted is not the same as being installed

`policy/tool-tiers.yaml` says what the risk broker is *permitted* to run. It
says nothing about what exists. Before `just doctor`, 28 of 34 allowlisted
tools were absent, so skills instructed the agent to run commands that could
not run.

A missing tool is not an error — the broker returns `executable not found`
cleanly — but any skill step naming it silently cannot be followed.

---

## EDA and PCB

| Tool | Does | Tier | Licence | Install |
|---|---|---|---|---|
| `kicad-cli` | ERC, DRC, Gerber/drill/pos/STEP export. The workhorse. | T1 | GPL-3.0 *(unverified here)* | `brew install --cask kicad` — **1.3 GB** |
| `kikit` | Panelisation, mouse-bites, V-cuts from KiCad files | T1 | MIT | `uv tool install kikit` |
| `kibot` | Declarative fab-output generation; drives kicad-cli from a YAML config. Good for making a board's outputs reproducible. | T1 | GPL-3.0 | `uv tool install kibot` |
| `pcbdraw` | Board renders and placement diagrams | T1 | MIT *(kikit ecosystem)* | `uv tool install pcbdraw` |
| `gerbv` | Gerber viewer — open what the fab will actually build | T1 | GPL-2.0-or-later | `brew install gerbv` ⚠️ |
| `ngspice` | SPICE simulation | T1 | BSD-style *(brew: "cannot represent")* | `brew install ngspice` |
| `kicost` | BOM costing from a KiCad BOM, across distributors | **T2** | MIT | `uv tool install kicost` |

⚠️ **`gerbv` is deprecated in Homebrew** (depends on EOL `gtk+`), scheduled for
disablement **2027-08-28**. It still installs and runs today. KiCad's own
Gerber viewer is the successor.

**Why `kicost` is T2, not T1.** It queries distributor APIs — it is an outbound
fetch that consumes someone else's service, not a local computation. Same
reasoning as `curl`.

## Firmware

| Tool | Does | Tier | Licence | Install |
|---|---|---|---|---|
| `esptool` | Flash, erase, chip info | T2 *(writes)* | GPL-2.0+ | `uv tool install esptool` |
| `espefuse` | eFuse read and burn | **T3** *(burn)* | GPL-2.0+ | ships with `esptool` |
| `esphome` | YAML-defined firmware; `compile` is T1, `run` flashes | T1 / T2 | unverified | `uv tool install esphome` |
| `arduino-cli` | `compile` T1, `upload` T2 | T1 / T2 | GPL-3.0-only | `brew install arduino-cli` |
| `pio` / `platformio` | `run` T1, `run -t upload` T2 | T1 / T2 | Apache-2.0 | `uv tool install platformio` |
| `idf.py` | ESP-IDF build/flash/monitor | T1 / T2 | Apache-2.0 *(unverified here)* | Espressif `get_idf` installer |
| `wokwi-cli` | Headless simulation | T1 | unverified | `curl -L https://wokwi.com/ci/install.sh \| sh` |

Note: **esptool v5 deprecated the `.py` suffixes** (`esptool.py` → `esptool`)
and moved to hyphenated subcommands (`write-flash`). Both forms are
allowlisted; write the new one.

**Known false positive:** `esptool ... read_flash` classifies T3 `unmatched`.
It is a read, so this is over-strict — but fixing it means *adding* a rule that
permits a device connection, which is a widening and therefore the repo owner's
call, not the agent's. Left as-is deliberately.

## Debug probes — not installed

Not part of the ESP32 stack, so deliberately skipped. `openocd`
(`brew install open-ocd`), `pyocd` (`uv tool install pyocd`), `picotool`
(`brew install picotool`), `avrdude` (`brew install avrdude`), `probe-rs`
(installer script — not in brew). All already allowlisted with rules; install
if you pick up an RP2040 or AVR board.

## Mechanical and enclosures

| Tool | Does | Tier | Licence | Install |
|---|---|---|---|---|
| `openscad` | Parametric CAD from code — fits a programmer better than sketch-based CAD | T1 | GPL-2.0 *(unverified here)* | `brew install --cask openscad` |
| `freecad` | Full parametric CAD, scriptable in Python | T1 | LGPL-2.1 *(unverified here)* | `brew install --cask freecad` |
| `admesh` | STL analysis and repair — check a mesh before slicing | T1 | GPL-2.0 *(unverified here)* | `brew install admesh` |
| `orcaslicer` / `prusa-slicer-console` / `CuraEngine` | Slicing. Produces gcode. | T1 | GPL-3.0 *(unverified here)* | `brew install --cask orcaslicer` |

**Slicing is T1; sending the gcode to a printer is T3.** Generating a file
changes nothing. Starting unattended machine motion with fire and injury risk
is a different act, and the tier boundary sits exactly there.

## Bring-up and instruments

| Tool | Does | Tier | Licence | Install |
|---|---|---|---|---|
| `sigrok-cli` | Logic analyser capture | T1 | GPL-3.0-or-later | `brew install sigrok-cli` |
| `mosquitto_pub` / `_sub` | MQTT publish / subscribe | T2 / T1 | EPL-1.0 OR BSD-3-Clause | `brew install mosquitto` |
| `i2cdetect` / `i2cget` | I²C bus scan and read | T1 | GPL-2.0 *(unverified)* | **Linux only** |
| `i2cset` | I²C write | T2 | GPL-2.0 *(unverified)* | **Linux only** |
| `gpioget` / `gpioset` | GPIO read / write via libgpiod | T1 / T2 | LGPL-2.1 *(unverified)* | **Linux only** |

**The I²C and GPIO tools will not work on a Mac.** They read `/dev/i2c-*` and
`/dev/gpiochip*`, which are Linux device nodes; a Mac has no such hardware.
Homebrew will install `i2c-tools` and it will find nothing. They belong on the
Raspberry Pi. They are allowlisted anyway because their tier rules already
existed, and a rule whose binary is refused is dead code.

## Documents and ingest

| Tool | Does | Tier | Licence | Install |
|---|---|---|---|---|
| `curl` / `wget` / `httpx` | Fetch a document | T2 | various | present or `brew install` |
| `trafilatura` | Readable text from static HTML | T2 | Apache-2.0 *(unverified here)* | `uv tool install trafilatura` |
| `docling` | Document and table extraction | T1 *(local)* | MIT *(unverified here)* | `uv tool install docling` |
| `pandoc` | Format conversion | T1 | GPL-2.0-or-later | `brew install pandoc` |
| `ollama` | Local models | T1 | MIT *(unverified here)* | `brew install ollama` |
| `rg` | The wiki's whole retrieval strategy | T1 | Unlicense | `brew install ripgrep` |

`pymupdf` is a Python library rather than a CLI, installed in the repo venv and
used directly by the ingest workflow.

---

## Adding a tool

1. Add the binary to `binaries_allowed` in `policy/tool-tiers.yaml`.
2. Give it a tier rule — **without one it falls to `default_tier: 3` and is refused.** That is the safe direction, not a working state.
3. Add a case to `CASES` in `harness/tests/test_tiers.py`; `test_every_rule_is_covered` fails if a rule has no test.
4. Add it here with its licence and the date you checked.

Widening the allowlist is a guardrail change. `REVIEW.md` §1.1 is what happens
when a guardrail is trusted without being tested.
