# plan.md — CIPHER Stage 3: Operations 06-08

<!--
SCOPE: Content layer only. Three new operations on the existing Stage 1 engine.
NOT HERE: Engine changes → cipher-stage1 (complete)
NOT HERE: AEGIS → separate spec track
-->

**Module:** cipher-stage3
**Date:** 2026-04-11
**Depends on:** cipher-stage1 (engine), cipher-stage2 (ops 01-05 complete)
**Modifies DATA_MODEL.md:** No
**Modifies CONSTITUTION.md:** No

---

## Problem

Stage 2 ended with the player cracking the admin password and reaching
`/admin/dashboard`. The Red Team track has no further operations.
Stage 3 completes the NexusCorp infiltration arc — moving from web
application attacks through privilege escalation to full system access.

---

## What We Are Building

Three new operations, all JSON-driven, all loaded by the existing engine.
No Python engine changes. Each op adds:
- One JSON file in `content/operations/`
- One tool function in `utils/tools.py`
- One entry in `content/registry.json`

---

## Story Arc — NexusCorp Infiltration (Conclusion)

| Op | Phase | What the player does |
|----|-------|---------------------|
| op01-05 | Initial access → credential attack | Caesar → Base64 → Port scan → Log analysis → Hash crack |
| op06 | Web enumeration | Directory brute-force on the admin panel web server |
| op07 | Web application attack | SQL injection on a login form found via enumeration |
| op08 | Privilege escalation | SUID/sudo misconfiguration on the compromised server |

The player enters Stage 3 with admin panel access. The arc:
- op06: Enumerate the admin panel server to find a hidden backup endpoint
- op07: SQL inject a login form discovered during enumeration to dump a user table
- op08: Exploit a SUID misconfiguration on the server to escalate to root

---

## Cert Objective Mapping (PenTest+ PT0-003)

| Op | Difficulty | Domain | Objective |
|----|-----------|--------|-----------|
| op06 | 3 | Domain 2 — Reconnaissance | Web application enumeration |
| op07 | 3 | Domain 3 — Attacks and Exploits | Web application attacks (SQLi) |
| op08 | 4 | Domain 3 — Attacks and Exploits | Post-exploitation / privilege escalation |

---

## Tool Functions to Build

| Op | tools_type | What it simulates |
|----|-----------|-------------------|
| op06 | `dir_enumerator` | Simulated directory brute-force scan (gobuster-style output) |
| op07 | `sqli_tester` | Tests a simulated SQL injection payload against a login form |
| op08 | `suid_scanner` | Simulates a find command scanning for SUID binaries |

---

## Phases

### Phase 1 — Tool functions (utils/tools.py)
Build all 3 new tool functions. Verify via check_imports.py.

### Phase 2 — Operation JSON files (content/operations/)
Write op06.json through op08.json. Each must pass validate_content.py.

### Phase 3 — Registry update (content/registry.json)
Add op06-op08 entries in order. Re-run validate_content.py.

### Phase 4 — Validation
Full suite: validate_content.py + check_imports.py + unit tests.
Automated end-to-end check for op06.

---

## Constraints

- Engine must not change
- All content uses the NexusCorp / CIPHER fictional universe (CONSTITUTION §5)
- All tool functions: stdlib only, return formatted string, use challenge_data
- Each op: exactly 4 hints (escalating), valid_answers normalized list
- Difficulty: 3, 3, 4
- xp_base increases: op06=200, op07=200, op08=250

---

## Definition of Done

- [ ] op06-op08 JSON files created and pass validate_content.py
- [ ] 3 new tool functions added to utils/tools.py
- [ ] registry.json updated with all 3 entries (total 8 ops)
- [ ] check_imports.py passes on all files
- [ ] All existing unit tests still pass
- [ ] Full op06 end-to-end check passes
- [ ] specs/cipher-stage3/spec.md status → Complete
