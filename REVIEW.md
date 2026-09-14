# REVIEW — hardware-agent scaffold

Read of every file in the scaffold, plus verification against this machine and
against vendor documentation. Nothing has been changed yet.

Conventions below: **[verified]** means I checked it against a primary source or
ran it here, and the source is cited. **[unverified]** means I believe it's
wrong or shaky but haven't yet confirmed it — those are Phase 2 work, and I've
kept them separate rather than dressing them up as findings.

---

## 1. What's wrong or unverifiable

### 1.1 The risk broker's two layers of defence are both bypassable — with one character  **[verified: ran it]**

This is the most serious thing in the repo, and it invalidates the claim the
README makes for the whole design.

`harness/risk_broker/tiers.py:56` inspects only the *first* shlex token:

```python
    @staticmethod
    def _binary(command: str) -> str | None:
        ...
        for part in parts:
            if "=" in part and not part.startswith("-"):
                continue
            return Path(part).name
```

`harness/risk_broker/server.py:50` then runs the *entire original string*
through a shell:

```python
    proc = subprocess.run(
        command,
        shell=True,
```

So everything after a `;` is invisible to classification and fully executed. I
ran this against the real `Policy` class:

```
T1 bin=kicad-cli allowed=True rule=eda | kicad-cli sch erc b.kicad_sch; rm -rf ~/Documents
```

**T1, binary allowed, `run_autonomous` would execute it.** The broker README
says the allowlist is "what stops `rm -rf /` and anything else that wanders in".
It does not. Neither layer sees past the first token.

Two smaller variants of the same root cause:

- `python` and `python3` are on the allowlist, and rule `kb-search` matches the
  bare substring `lint\.py` (`policy/tool-tiers.yaml:141`). So
  `python3 /tmp/lint.py` is **T1 arbitrary code execution**. Verified.
- Rule `build` matches the bare substring `compile`, `read-only-instrument`
  matches bare `monitor`. Any path containing those words upgrades a command to
  T1. The rules match against free text, not against a parsed argv.

This is the one finding I'd fix before using the repo for anything at all.

### 1.2 `server.py` cannot import on a fresh install  **[verified]**

`harness/risk_broker/server.py:30`:

```python
from mcp.server.fastmcp import FastMCP
```

MCP Python SDK **2.0.0 removed `mcp.server.fastmcp` and renamed `FastMCP` →
`MCPServer`**. The current quickstart is `from mcp.server import MCPServer`.
Latest release is 2.2.0. And `harness/risk_broker/README.md:11` says:

```bash
pip install "mcp[cli]" pyyaml
```

Unpinned — so a fresh install resolves to 2.x and the server dies on import.
The scaffold was only ever tested with a stubbed `mcp`, which is exactly why
this survived. Decorator and handler signatures are unchanged, so the migration
is small.

Confirmed on this machine: `mcp` is **not installed** (`ModuleNotFoundError`),
`pyyaml` 6.0.3 is, Python is 3.12.6, `uv` 0.11.3 is present, `just` is **not**.

### 1.3 JLCPCB numbers  **[verified against jlcpcb.com/capabilities/pcb-capabilities]**

`skills/manufacturing-dfm/references/jlcpcb-capabilities.md` is the file AGENT.md
tells the agent to read "before claiming a trace width is manufacturable", so
its errors propagate directly into design advice.

| Repo says | Actually published | Verdict |
|---|---|---|
| `1-2 layer, 1 oz: 5 mil (0.127 mm)` | **4/4 mil (0.10 mm)** | Wrong — outdated, conservative |
| `Multilayer: 3.5 mil (0.0889 mm)` | 3.5/3.5 mil (0.09 mm) | Correct |
| `Minimum via hole: 0.15 mm` | 0.15 mm for **2-layer and up**, flagged "more costly"; **1-layer is 0.3 mm** | Missing its qualifier |
| `paired with at least a 0.15 mm annular ring` | Min PTH annular ring **≥0.20 mm**; the 0.15 mm via has a 0.25 mm diameter = 0.05 mm ring per side | **Wrong** |
| `Minimum solder-mask dam: ~0.2 mm` | Min pad spacing 0.10 mm @1 oz, 0.20 mm @2 oz | Conservative, mislabelled |

The annular-ring line is the one to care about — it's wrong in the direction
that makes a design look compliant when it isn't.

The same wrong 5 mil / 0.15 mm ring figures are repeated verbatim in
`skills/manufacturing-dfm/SKILL.md:54`. Duplicated numbers drift; this should
live in one place.

### 1.4 The 70×70 mm panelization rule is stated backwards  **[verified]**

`skills/manufacturing-dfm/SKILL.md:26` — "Below roughly 70×70 mm, boards are
panelized for assembly" — and the same claim in `jlcpcb-capabilities.md:25`.

What JLCPCB actually publishes: **70×70 mm is the minimum board size for
*Standard* PCBA**, and boards under it need panelization or process edges to
*reach* 70×70. **Economic PCBA accepts 10×10 mm.** For your volumes Economic is
very likely the service you'd use, so the repo's framing pushes you toward
panelization work you may not need, on the service you probably aren't buying.

### 1.5 `idf.py secure-boot-enable` is not a real command  **[verified against Espressif docs]**

`skills/firmware/references/esp32-irreversible.md:22`. There is no such
subcommand. Secure Boot v2 is enabled via menuconfig, then `idf.py bootloader`,
then flashing — and the `ABS_DONE_1` eFuse is set *by the bootloader on first
boot*, not by a command. The real `idf.py` security subcommands are
`secure-generate-signing-key`, `secure-sign-data`, `secure-verify-signature`.

This matters more than a typo would, because smoke test #3 ("enable secure boot
on the production units") is supposed to *draft the exact command*. Drafting a
command that doesn't exist, with full T3 ceremony around it, is worse than
drafting nothing — it looks authoritative.

Related: the fact that enabling happens at first boot rather than at a command
is itself the safety-relevant detail, and the reference file doesn't say it.

### 1.6 esptool `.py` suffixes are deprecated  **[verified]**

esptool v5 deprecated `esptool.py` / `espefuse.py` / `espsecure.py` in favour of
the bare console scripts. They still work but emit deprecation warnings and are
slated for removal in the next major. Every example in `skills/firmware/SKILL.md`
and `esp32-irreversible.md` uses the `.py` form. The allowlist in
`policy/tool-tiers.yaml:24-27` happens to carry both, so the broker is fine —
it's the drafted commands that will rot.

### 1.7 The flash offset in the T2 example is wrong for ESP32 classic  **[verified]**

`skills/firmware/SKILL.md:87`:

```bash
esptool.py --port /dev/cu.usbmodem1101 write_flash 0x0 firmware.bin
```

`0x0` is the bootloader offset on C3/C6/S3; on **ESP32 classic it's 0x1000**,
and an application image normally goes at 0x10000 with a partition table at
0x8000. As written this is a command that quietly produces a non-booting board
on the one part family the wiki's seeded entry is about.

### 1.8 The seeded wiki entry has a provenance problem the linter cannot see  **[verified reasoning; symptom claim clarified below]**

`wiki-template/wiki/hardware/fm-esp32-brownout-boot-loop.md:18-23` cites:

```yaml
  - title: "ESP32 Series SoC Errata"
    publisher: Espressif
    section: "chip revision identification"
    trust: high
```

The cited section is about **identifying chip revisions**. It does not support a
claim about brownout behaviour under LED inrush. But because it's the only
`trust: high` source, it is what licenses `confidence: high` past `lint.py:119`.

The entry passes the linter while violating rule 3 of its own
`trust-and-provenance.md` ("Elevation to `high` requires a vendor-authoritative
source" — for *this claim*, not for any claim). This is the seeded example,
which means it's the template every future entry imitates. It teaches the exact
habit the trust model exists to prevent.

I'd rather fix this entry than weaken the rule: cite the ESP32 TRM / datasheet
section that actually documents the brownout detector, or drop to
`confidence: medium`.

**A correction to my own first read**, since it cuts the other way: I initially
flagged `rst:0xc (SW_CPU_RESET)` (line 11) as simply wrong, expecting
`rst:0xf (RTCWDT_BROWN_OUT_RESET)`. It isn't wrong. There's a documented
ESP-IDF issue where the brownout handler resets via the watchdog and the boot
ROM then reports `SW_CPU_RESET`, so `rst:0xc` is genuinely observed. The real
defect is narrower and more interesting: **`rst:0xf` is missing from the symptom
list**, so `rg "rst:0xf" wiki/` — the exact search a person does when staring at
their serial monitor — finds nothing. For a wiki whose entire retrieval strategy
is grep, an incomplete symptom list *is* a broken index.

### 1.9 Unverified, flagged rather than asserted  **[Phase 2]**

I have not checked these and won't claim them either way yet:

- `led-power-thermal.md:10` — "Efficacy: ~30-40 lm/W for WS2812B, versus 120+
  lm/W for a plain 2835". Both numbers are unsourced and the 2835 figure looks
  optimistic for cheap strips. This drives a *product* recommendation
  (addressable = accent only), so it should be sourced.
- `led-power-thermal.md:9` and `circuit-design/SKILL.md:27` say a 60 LED/m strip
  **"dissipates ~18 W per metre"**. 3.6 A × 5 V = 18 W is *drawn*, not
  dissipated — some fraction leaves as light. Small point, but this is a
  thermal-budget file and the distinction is the whole subject.
- `sourcing-bom/SKILL.md:58` — the Nexar free-tier limits (lifetime 1,000 parts,
  new apps default to 0, ~$500/mo paid) are specific enough to be checkable and
  come from "third-party trackers". Verify or soften.
- WS2812B 60 mA/LED and the 0.7×VDD logic threshold both look right to me but
  should get a datasheet citation like everything else.

---

## 2. What's missing

- **Tests. There are none.** `risk_broker/README.md:60` literally says
  `python -m pytest tests/   # if you add them`. For the one component whose
  entire job is refusing dangerous things, this is the gap that let §1.1 exist.
- **No dependency manifest**, no lockfile, no `.gitignore`, no task runner. Not
  a repo yet.
- **`subprocess.TimeoutExpired` is uncaught** (`server.py:50`). A hung
  `idf.py build` takes down the tool call with a traceback instead of a message.
- **`_execute` captures output with no size guard before slicing.** A build that
  emits 500 MB of logs is buffered entirely in memory before `[-20000:]`.
- **The audit log never rotates** and defaults to `~/.risk-broker-audit.jsonl`,
  outside the repo, while the README example puts it inside. Pick one.
- **`wiki/parts/` is created by `bootstrap.sh:19` but never seeded.** The `part-`
  schema has never met a real document — which is precisely what Phase 3's
  ESP32-C6 ingest will stress. Expect the schema to need changes there; that's
  the test working.
- **No guidance on what happens when the broker refuses something legitimate.**
  The stated policy is "add a rule rather than working around a refusal", but
  nothing describes reviewing that rule change, which is itself a guardrail edit.

---

## 3. What's over-built

Less than I expected, honestly. The risk model and the trust model both earn
their complexity. These are the exceptions:

- **`recent_actions` (`server.py:206`)** is a tool that reimplements
  `tail ~/.risk-broker-audit.jsonl`. It costs a tool slot in every context
  window for the life of the project. Cut it.
- **The RPN arithmetic check (`lint.py:134`)** validates that a number you typed
  equals the product of three other numbers you typed. It has never caught a
  real error because the failure mode of FMEA scoring isn't arithmetic, it's
  optimism. Either compute `rpn` rather than validating it, or drop the field.
- **`README.md:74-84` "Open questions"** duplicates `CLAUDE-CODE-PROMPT.md`.
  One of the two should go — and `CLAUDE-CODE-PROMPT.md` shouldn't ship in the
  repo at all, let alone twice (there's an identical copy one directory up).
- **`AGENT.md` and `guardrails.md` restate each other** at roughly 70% overlap —
  mains, lithium, money, compliance, simulation, grounding all appear in both,
  sometimes in near-identical words. The duplication is a maintenance trap: you
  will eventually fix one and not the other. `AGENT.md` should carry routing and
  tiers; `guardrails.md` should carry the stances, once.

---

## 4. Where the skill boundaries are wrong

**`research-and-ingest` + `knowledge-base` → merge.** These are one pipeline:
fetch → extract → draft → gate. They share a vocabulary (`trust`, provenance,
retrieval date), and `research-and-ingest/SKILL.md:80` already has to explain
the other skill's gate to make sense of itself. Worse, the handoff *is* the
seam where provenance gets dropped, and a skill boundary across it means the
model can load one half without the other. Merging makes the provenance rules
unconditionally present at the moment a document is being read.

**`sourcing-bom` + `manufacturing-dfm` → keep separate.** They genuinely answer
different questions at different stages: "can I get this part and what does it
cost" versus "can a factory build this board". The overlap you noticed is
real but small and specific — LCSC basic/extended status, which appears in
both. Fix the overlap by making it a single shared reference file that both
point to, rather than by merging two skills that are each already near the
right size.

One boundary problem you didn't raise: **`circuit-design` currently owns
antennas and RF keep-outs, while `manufacturing-dfm` owns ANATEL.** For your
work those are the same decision — module choice, antenna placement and
homologation scope are one call made once. Whichever way the merges go, that
decision needs a single home.

---

## 5. The disagreement I owe you

You said the T3 gate on wiki writes stays. I agree with it, and I'm not asking
you to soften it. But **it is not enforced where the repo says it is.**

`policy/tool-tiers.yaml:53` guards canonicalisation like this:

```yaml
    match: '\b(cp|mv|tee|rsync|install)\b.*\bwiki/|>>?\s*\S*wiki/|kb[_-]?canonicalize'
```

That catches *shell commands*. An agent in Claude Code writes files with the
**Write tool**, which never passes through the broker at all. So the rule guards
a path the agent won't take. I verified the shell path does classify T3 — it
does — but that's not the path that matters.

The only real gate is the wiki repo's pre-commit hook, and as shipped it has two
defects (`harness/kb/bootstrap.sh`):

1. **Lines 22-25 run `git init`, `git add -A`, `git commit` *before* line 29
   installs the hook.** The seeded entry — the template for everything after
   it — enters the wiki having never passed the linter.
2. **Line 33's path doesn't resolve.**
   `$(git rev-parse --show-toplevel)/../hardware-agent/harness/kb/lint.py` for a
   wiki at `~/wiki-hardware` points at `~/hardware-agent/...`. Your instinct was
   right.

   Two distinct failure modes follow, and they're worth separating:

   - **Missing linter, python3 present:** `python3` exits non-zero ("can't open
     file"), the `|| { ... exit 1; }` block fires, and the commit *is* blocked —
     but the message printed is "Wiki lint failed. Fix the entries above", which
     blames your entry for a broken install path. You'd go looking in the wrong
     place.
   - **python3 absent:** line 32's `if command -v python3` guard skips the whole
     block and the hook **exits 0**. The gate silently disappears. A guardrail
     whose absence is indistinguishable from success is the failure mode worth
     designing against — the hook should fail loudly when it cannot run the
     linter, not treat "couldn't check" as "checked and fine".

So: the guardrail is in the wrong place. I'm proposing to **move** it, not to
file its edges off:

- Make the hook correct — bake the absolute resolved path in at bootstrap time,
  install it *before* the first commit, and fail loudly if the linter is missing
  rather than treating absence as a pass.
- Keep the YAML rule as defence-in-depth.
- Add a deny on Write/Edit targeting `wiki/` so the tool path is covered too.

Net effect is a **stronger** gate than today. Flagging it explicitly because
you asked me to argue rather than quietly reroute.

---

## 6. The five decisions — my recommendations

**1. Merges.** `research-and-ingest` + `knowledge-base`: **yes**, reasoning in
§4. `sourcing-bom` + `manufacturing-dfm`: **no** — extract the shared LCSC
basic/extended material into one reference instead.

**2. Is the T3 wiki gate too heavy?** **Keep it; fix the ergonomics instead.**
The README's own suggestion (`README.md:83`) is to auto-approve
`confidence: low` entries — that weakens exactly the wrong thing, since low
confidence marks the entries *most* likely to be wrong. The cost you're feeling
isn't the review, it's the ceremony around it. Make approval one command that
shows you the diff and commits on a keystroke, and a gate that costs ten seconds
stops being the reason you don't write entries.

**3. `raw/` in git?** **No — gitignore it.** Record `sha256` + URL + retrieval
date in the entry's frontmatter instead. You get reproducibility (you can prove
which document you read, and detect when it changes) without putting
third-party PDFs in your history permanently. This is also what
`legal-and-etiquette.md:19` already argues for — "keep them private, prefer
extracted facts plus a page reference over a stored copy" — so tracking `raw/`
would contradict the repo's own stated posture.

**4. Scraping stack?** **Neither, yet.** Your actual workload is vendor PDFs
from docs.espressif.com and nxp.com — static files that `httpx` + `pymupdf`
handle without a browser. Self-hosting Crawl4AI is infrastructure you'd
maintain for a workload you don't have. Add **Firecrawl's hosted MCP** as the
escape hatch the first time a page genuinely fights back. If that never
happens, you've saved the whole thing.

**5. `enclosure-design` skill?** **Not yet.** Today it'd be a thin wrapper over
two slicer commands and the PLA-softens-at-60 °C note. Split it when you have
enough printed-optics and diffuser material to fill it — for a lighting product
that may well happen, but let the content justify the file rather than the
reverse.

---

## 7. What I'd fix first, in order

1. The broker injection hole (§1.1). Everything else is cosmetic next to it.
2. The MCP SDK migration (§1.2) — the server does not currently start.
3. Tests, including a regression test for §1.1.
4. `bootstrap.sh` ordering and hook path (§5).
5. The JLCPCB numbers (§1.3, §1.4) and the secure-boot command (§1.5), since
   those are what the agent will actually say to you.
6. Everything else.

---

## 8. Two notes on the environment

- **`just` is not installed**; `make` is. Your definition of done says
  `just setup && just test && just lint`. Homebrew is available, so this is one
  install — flagged because it's a dependency your stated acceptance criteria
  assume.
- **The scaffold lives in `~/Downloads/hardware agent/`, and the parent
  directory name contains a space.** That has already broken one thing and will
  break more shell quoting. Moving to `~/dev/hardware-agent` as agreed.

---

*Phase 0 complete. Nothing changed. Awaiting your response before Phase 1.*
