# plan.md — AEGIS Stage 1: Core Engine + Cases 01-05

<!--
SCOPE: Full AEGIS engine + five cases covering CySA+ CS0-003 Domains 1-3.
NOT HERE: AEGIS Stage 2+ → future spec
NOT HERE: CIPHER → cyberforge/cipher/
-->

**Module:** aegis-stage1
**Date:** 2026-04-11
**Depends on:** cipher-stage1 architecture (reuse patterns, not code)
**Modifies DATA_MODEL.md:** Yes — AEGIS save file location, exam_tip field already defined

---

## Problem

There is no AEGIS game yet. Students studying for CySA+ have the CIPHER
Red Team track but no Blue Team counterpart. Stage 1 builds the full
AEGIS engine and five playable cases covering the core SOC analyst
skills mapped to CySA+ CS0-003 Domains 1-3.

---

## What We Are Building

AEGIS is a separate game in `cyberforge/aegis/`. It follows the identical
engine architecture as CIPHER (JSON-driven, stdlib only, same command set)
but with Blue Team content — cases instead of operations, analyst framing
instead of attacker framing, and an `exam_tip` field in every debrief.

### Key differences from CIPHER

| | CIPHER | AEGIS |
|--|--------|-------|
| Player role | Attacker (red team) | Defender (SOC analyst) |
| Content unit | Operation | Case |
| Content dir | content/operations/ | content/cases/ |
| Fictional company | NexusCorp (target) | Veridian Systems (employer) |
| Debrief extra field | none | exam_tip |
| Cert | PenTest+ PT0-003 | CySA+ CS0-003 |

---

## Story Arc — The NexusCorp Attack (Defender Side)

The player is a SOC analyst at Veridian Systems. The five cases are the
same NexusCorp infiltration from CIPHER — but seen from the defender's
perspective. Each case presents the evidence the SOC analyst would have
seen and asks them to identify, classify, and respond to it.

| Case | What the analyst sees | Mirrors CIPHER op |
|------|-----------------------|-------------------|
| case01 | Web server logs with suspicious 200s from an internal IP | op04 Access Logs |
| case02 | An encoded string found in a config file — classify the IOC | op02 Vault Secrets |
| case03 | A vulnerability scan report showing an unpatched web server | op03 Network Sweep |
| case04 | A process list showing an unexpected python3 SUID process | op08 Root Access |
| case05 | An IR ticket — determine the correct response phase | op01-08 full arc |

---

## Cert Objective Mapping (CySA+ CS0-003)

| Case | Difficulty | Domain | Objective |
|------|-----------|--------|-----------|
| case01 | 1 | Domain 1 — Security Operations | Log analysis and threat detection |
| case02 | 1 | Domain 1 — Security Operations | IOC identification and classification |
| case03 | 2 | Domain 2 — Vulnerability Management | Vuln scan interpretation and prioritization |
| case04 | 2 | Domain 1 — Security Operations | Malware/anomaly detection in process data |
| case05 | 3 | Domain 3 — Incident Response | IR lifecycle phase identification |

---

## Engine Components to Build

AEGIS gets its own engine. It shares the same architecture patterns as
CIPHER but lives in `aegis/` with its own files. No code sharing between
games — CONSTITUTION §3 rule 4 (shared utils, not shared state).

| File | Purpose |
|------|---------|
| `aegis/main.py` | Entry point, menu router |
| `aegis/engine/case_runner.py` | Generic case engine (reads any case JSON by ID) |
| `aegis/utils/terminal.py` | Same interface as cipher — copy of pattern |
| `aegis/utils/player.py` | XP + badge evaluation |
| `aegis/utils/save_manager.py` | Save/load/backup/migration |
| `aegis/utils/tools.py` | AEGIS tool functions (log_filter, ioc_classifier, vuln_scorer, process_analyzer) |
| `aegis/content/cases/case01-05.json` | Five case content files |
| `aegis/content/registry.json` | Case registry |
| `aegis/content/placement_test.json` | CySA+ placement test |
| `aegis/validate_content.py` | Schema validator (AEGIS version, includes exam_tip) |
| `aegis/check_imports.py` | Stdlib import auditor |
| `aegis/tests/test_save_manager.py` | Save manager unit tests |

---

## Phases

### Phase 1 — Engine infrastructure (utils + tests)
terminal.py, player.py, save_manager.py + tests, check_imports.py

### Phase 2 — Tool functions (utils/tools.py)
4 tool functions: log_filter, ioc_classifier, vuln_scorer, process_analyzer

### Phase 3 — Content layer (cases + registry + placement test)
case01-05.json, registry.json, placement_test.json, validate_content.py

### Phase 4 — Case engine + main menu
case_runner.py (full command loop), main.py (all flows)

### Phase 5 — Validation
Full suite + manual playthrough case01

---

## Constraints

- Pure Python 3.8+ stdlib only — same allowlist as CIPHER
- Zero code imports between aegis/ and cipher/ — fully independent
- AEGIS cases include exam_tip in debrief — CIPHER ops do not
- All content uses Veridian Systems / AEGIS fictional universe
- Same 9-command interface as CIPHER (help, learn, tools, hint, notes,
  note, skip, menu, quit)
- Same atomic save pattern as CIPHER
- xp_base: case01=100, case02=100, case03=150, case04=150, case05=200

---

## Definition of Done

- [ ] `python main.py` launches AEGIS and shows main menu
- [ ] Full case01 playthrough works end-to-end
- [ ] All 5 cases visible in case menu
- [ ] `validate_content.py` passes on all content
- [ ] `check_imports.py` passes on all files
- [ ] All unit tests pass
- [ ] specs/aegis-stage1/spec.md status → Complete
