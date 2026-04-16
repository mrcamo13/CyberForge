# plan.md — CIPHER Stage 2: Operations 02-05

<!--
SCOPE: Content layer only. No engine changes.
       Four new operations built on top of the Stage 1 engine.
NOT HERE: Engine changes → cipher-stage1 (complete)
NOT HERE: AEGIS → separate spec track
-->

**Module:** cipher-stage2
**Date:** 2026-04-11
**Depends on:** cipher-stage1 (engine must be complete and passing)
**Modifies DATA_MODEL.md:** No — tools_type entries already registered

---

## Problem

Stage 1 proved the engine end-to-end with one operation.
The game currently has only op01. Players complete it and have nowhere to go.
Stage 2 fills the Red Team curriculum from entry-level encoding through
credential attacks — the core of PenTest+ Domain 2 and Domain 3.

---

## What We Are Building

Four new operations, all JSON-driven, all loaded by the existing engine.
No Python engine changes. Each op adds:
- One JSON file in `content/operations/`
- One tool function in `utils/tools.py`
- One entry in `content/registry.json`

---

## Story Arc — NexusCorp Infiltration (Continuous)

All four operations continue directly from op01. The player decoded the
vault password and is now inside NexusCorp's systems. The mission escalates
with each operation, following a realistic pentest kill chain:

| Op | Phase | What the player does |
|----|-------|---------------------|
| op01 | Initial Access | Decode vault password (Caesar cipher) |
| op02 | Reconnaissance | Decode a Base64 credential found in the vault |
| op03 | Network Mapping | Simulate a port scan on NexusCorp's internal subnet |
| op04 | Log Analysis | Analyze a web server log to find the admin panel path |
| op05 | Credential Attack | Crack an MD5 hash found in a config file |

Each operation opens with a transmission from GHOST continuing the story.
Each debrief connects the technique to the next operation.

---

## Cert Objective Mapping (PenTest+ PT0-003)

| Op | Difficulty | Domain | Objective |
|----|-----------|--------|-----------|
| op02 | 1 | Domain 2 — Reconnaissance | Encoding/decoding in recon context |
| op03 | 2 | Domain 2 — Reconnaissance | Network scanning and enumeration |
| op04 | 2 | Domain 2 — Reconnaissance | Log analysis and OSINT techniques |
| op05 | 3 | Domain 3 — Attacks | Credential attacks and hash cracking |

---

## Tool Functions to Build

Each op requires one new function in `utils/tools.py`:

| Op | tools_type | What it simulates |
|----|-----------|-------------------|
| op02 | `base64_decoder` | Decodes a Base64 string and displays the result |
| op03 | `port_scanner` | Shows a simulated port scan output for the challenge IP |
| op04 | `log_analyzer` | Parses a simulated log snippet and highlights patterns |
| op05 | `hash_cracker` | Runs a simulated MD5 dictionary attack against the hash |

All tool functions must follow the existing pattern in `utils/tools.py`:
- Accept `challenge_text: str` as input
- Return a formatted string
- Be registered in `run_tool()` dispatch table
- No external libraries — stdlib only

---

## Phases

### Phase 1 — Tool functions (utils/tools.py)
Build all 4 new tool functions and verify via `check_imports.py`.

### Phase 2 — Operation JSON files (content/operations/)
Write op02.json through op05.json using the NexusCorp story arc.
Each file must pass `validate_content.py` individually.

### Phase 3 — Registry update (content/registry.json)
Add op02-op05 entries to registry in order. Re-run validate_content.py.

### Phase 4 — Validation
Run full suite: validate_content.py + check_imports.py + unit tests.
Manual playthrough of op02 end-to-end.

---

## Constraints

- Engine (main.py, operation_runner.py, save_manager.py) must not change
- All content uses the NexusCorp / CIPHER fictional universe (CONSTITUTION §5)
- All tool functions: stdlib only, return formatted string
- Each op: exactly 4 hints (escalating), valid_answers normalized list
- Difficulty follows curriculum order: 1 → 2 → 2 → 3
- Each debrief references the next operation to maintain story continuity

---

## Definition of Done

- [ ] op02-op05 JSON files created and pass validate_content.py
- [ ] 4 new tool functions added to utils/tools.py
- [ ] registry.json updated with all 4 entries
- [ ] check_imports.py passes on all files
- [ ] All existing unit tests still pass
- [ ] Full op02 playthrough works end-to-end
- [ ] specs/cipher-stage2/spec.md status → Complete
