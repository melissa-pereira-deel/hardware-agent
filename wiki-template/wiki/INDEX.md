# Wiki index

The map. Maintained by hand. This is what makes grep work - it gives you (and
the agent) the vocabulary of the wiki, so you know what to search for.

Add an entry here whenever you add an entry to the wiki. An unindexed entry is
an entry nobody finds.

## Hardware / failure modes

- `fm-esp32-brownout-boot-loop` - ESP32 resets under LED inrush. Power problem wearing a firmware problem's clothes.

## Parts

*(nothing yet)*

## Procedures

*(nothing yet)*

## Devices

*(nothing yet)*

---

## Conventions

- `fm-` failure mode, `part-` part, `proc-` procedure, `dev-` device
- Symptoms in frontmatter are verbatim strings - error messages exactly as they appear
- Every entry is scoped with `applies_to`. An unscoped hardware fact is usually a wrong one.
- `confidence: high` requires a `trust: high` source. Forums never qualify.
