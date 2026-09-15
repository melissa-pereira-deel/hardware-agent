---
name: firmware
description: Write, build, flash and debug embedded firmware for ESP32 (ESP-IDF, Arduino, ESPHome), Arduino boards, RP2040 and Raspberry Pi Linux — including FreeRTOS task design, BLE GATT, Matter/Thread, MQTT, deep sleep and power optimisation, OTA updates and rollback, provisioning, and hardware bring-up debugging. Also covers device security and factory programming — secure boot, flash encryption, eFuse burns, and enabling any of these on production units — all of which are irreversible and advisory-only. Use this skill for anything involving firmware code, a serial monitor, a flash command, a board that won't boot, a device that drains its battery too fast, or a decision between Arduino and ESP-IDF. Also use it when the question is "why is this device behaving like that?" and the answer lives in software running on a microcontroller.
---

# Firmware

## Concepts

**Arduino and ESP-IDF are different maturity stages, not rival religions.**
*Analogy: Arduino is a managed platform where the runtime is handled for you;
ESP-IDF is the bare platform where you own the scheduler and the event loop.*
Arduino collapses FreeRTOS into effectively one task, which is fine until Wi-Fi
and BLE compete and you get priority-inversion bugs that are near-impossible to
diagnose. **Prototype in Arduino; move to ESP-IDF for production** when you
need secure boot, OTA with rollback, Wi-Fi/BLE coexistence, serious deep-sleep
optimisation, or reproducible factory programming. Arduino-as-an-ESP-IDF-
component is the migration path that doesn't throw away the driver code.

**Power is an energy budget, not a mode.** *Analogy: a monthly budget where
deep sleep is staying home and the radio is the expensive night out.* Battery
life comes from (active current × duty cycle) + (sleep current × the rest) +
self-discharge. A device that sleeps at 10 µA but wakes for 200 ms of Wi-Fi TX
every minute is dominated entirely by the radio. Model this before promising
anyone a battery-life number.

**OTA without rollback is a way to brick a fleet remotely.** The pattern that
works: two slots, atomic image swap, boot the new image, require the
application to *confirm* itself (usually after it successfully reaches the
network), and automatically revert if it doesn't. Add downgrade prevention so
an old vulnerable image can't be pushed back.

**ESPHome is the fastest route to a working smart-home prototype.** YAML
device definition, native Home Assistant integration, OTA built in. For a
lamp prototype it can compress a week of firmware into an afternoon. The
tradeoff is that you inherit its architecture — fine for prototypes and
small-batch products, limiting if you need custom BLE or tight power control.

**Raspberry Pi in a product is Linux engineering, not Pi engineering.** Use
device-tree overlays rather than poking registers, `libgpiod` rather than the
deprecated sysfs GPIO interface, systemd units rather than rc.local, and a
**read-only root filesystem** — SD cards corrupt when power is cut mid-write,
and products get their power cut.

## Decisions

**Which ESP32?** C3 for cheap Wi-Fi/BLE. S3 for more RAM, USB and AI/DSP work.
**C6 when you want Thread/Zigbee/Matter** — this is the one for smart lighting
that should join a Matter network. H2 for Thread/Zigbee without Wi-Fi.

**Matter or just MQTT?** Matter gets you native Apple/Google/Amazon support and
no app requirement, at the cost of a real certification process — CSA
membership, a Vendor ID, an authorised test lab, and a Distributed Compliance
Ledger listing, all *on top of* ANATEL. MQTT plus Home Assistant gets you a
working product for the enthusiast market with zero certification. Prototype on
MQTT/ESPHome, decide on Matter once the product is proven.

**Where does state live?** Decide explicitly whether the MCU, the phone, or the
cloud is authoritative, and what happens when the network is gone. A lamp that
can't be switched on without the internet is a defect.

## Traps

- **Blocking calls in a callback.** Watchdog resets that look like hardware faults.
- **`delay()` in anything real.** Use timers, tasks, or an event loop.
- **Flash writes in a loop.** Flash endurance is finite; wear-level or use NVS properly.
- **Debugging a power problem in software.** If it resets when a load switches on, it's a current budget problem in the circuit, not a bug. See `circuit-design`.
- **Forgetting the brownout detector exists.** Its threshold is configurable and it will hide as a mystery reboot.
- **Assuming the emulator is the chip.** Hosted emulators have shipped wrong RAM sizes at wrong addresses. Confirm timing, power and peripheral behaviour on real silicon.

## Tools

Install, licence and tier for every tool named here: `TOOLS.md`.
`just doctor` says which are present on this machine.

**T1 — run freely:**
```bash
arduino-cli compile --fqbn esp32:esp32:esp32c6 .
pio run                      # build all envs
idf.py build
esptool.py image_info firmware.bin
esphome compile lamp.yaml
wokwi-cli .                  # headless simulation with scenario YAML
```
Plus static analysis, unit tests, and reading a serial monitor or
sigrok/PulseView capture.

**T2 — confirm first (state which physical device, and how to recover):**
```bash
idf.py -p /dev/cu.usbmodem1101 flash    # prefer this: it uses the offsets the build computed
esptool --port /dev/cu.usbmodem1101 write-flash 0x10000 app.bin
pio run -t upload
arduino-cli upload -p /dev/cu.usbmodem1101 --fqbn ...
esphome run lamp.yaml
openocd / probe-rs / pyocd / picotool   # program, halt, reset
```

**Flash offsets are part-family specific — do not recall them.** The bootloader
sits at **0x1000 on ESP32 and ESP32-S2**, but at **0x0 on C3, C6, H2 and S3**.
Partition table is 0x8000 and the app 0x10000 on all of them. Flashing a
bootloader to 0x0 on an ESP32 classic produces a board that does not boot and
looks like a hardware fault. `idf.py flash` reads the offsets from the build,
which is why it is the right default; hand-written `write-flash` offsets are
where this goes wrong.

**Tool naming:** esptool v5 deprecated the `.py` suffixes (`esptool.py`,
`espefuse.py`) in favour of bare console scripts, and moved to hyphenated
subcommands (`write-flash`). The old forms still work but warn, and are slated
for removal in the next major. Write the new form.
Also T2: GPIO writes via `libgpiod`, I2C/SPI writes, BLE writes via `bleak`,
MQTT publishes to live devices, Home Assistant service calls.

**T3 — draft the command, explain, and stop:**
```bash
espefuse burn_key ...           # IRREVERSIBLE
espefuse burn_efuse ...         # IRREVERSIBLE
# enabling secure boot / flash encryption — note there is no single command;
# it is a menuconfig setting plus a first boot. See the reference.
avrdude -U lfuse:w:...          # can make a chip unreachable without HV programming
```
Read `references/esp32-irreversible.md` before even drafting these.

## Bring-up order

When a new board arrives, resist the urge to flash the application:

1. Power rails measured with a meter, unpowered continuity check first.
2. Current draw at idle — compare against the budget.
3. Blink an LED. Confirm the toolchain, the bootloader, and the clock config.
4. One peripheral at a time, simplest first (I2C scan before I2C driver).
5. Radio last.

Measure, don't guess. Bisect when something fails — halve the system, not the
code.

## Connections

- Pin assignments and bus choices come from `circuit-design` as a frozen contract.
- Secure boot, provisioning and factory programming belong to `manufacturing-dfm` as much as here.
- Module choice is jointly a `sourcing-bom` and certification decision.
