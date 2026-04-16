# plan.md — AEGIS Stage 3: Cases 14-21
<!--
SDD Phase 1 of 4: Plan
Next: spec.md → tasks.md → build
-->

**Module:** aegis-stage3
**Date:** 2026-04-12
**Depends on:** aegis-stage2 (cases 01-13, full engine)
**Adds to:** aegis/content/cases/, aegis/utils/tools.py, aegis/validate_content.py

---

## 1. What problem does this solve?

Stage 1 and 2 covered:
- Domain 1: log analysis, IOC correlation, ATT&CK mapping, C2 beaconing, network traffic
- Domain 2: vulnerability scoring, firewall gaps, risk scoring (all cases)
- Domain 3: only one case (case05 — IR phase identification)
- Domain 4: exec reporting, remediation ordering, breach notification (all cases)

**Domain 3 (Incident Response) is the largest gap.** It covers 22% of the CySA+ exam
but only has 1 case in Stage 1+2. Domain 1 also has gaps in SIEM correlation and
hypothesis-driven threat hunting — the most practical daily SOC analyst skills.

Stage 3 fills both:
- **Domain 1 depth**: SIEM alert triage, log source identification, threat hunting
- **Domain 3 coverage**: memory forensics, disk forensics, chain of custody,
  containment strategy, incident timeline reconstruction

---

## 2. Cases Overview

8 cases: case14-21. Difficulty 3-4 throughout (no reset — analysts are experienced now).

| Case | Title | Domain | Cert Objective | Difficulty | tools_type |
|------|-------|--------|---------------|------------|-----------|
| case14 | SIEM Triage | Domain 1 — Security Ops | Correlate and triage SIEM alerts | 3 | `siem_correlator` |
| case15 | Log Sources | Domain 1 — Security Ops | Identify correct log source for each event type | 3 | `log_classifier` |
| case16 | Threat Hunt | Domain 1 — Security Ops | Apply hypothesis-driven threat hunting methodology | 4 | `hunt_analyzer` |
| case17 | Memory Forensics | Domain 3 — Incident Response | Analyze memory artifacts for malicious indicators | 3 | `mem_analyzer` |
| case18 | Disk Forensics | Domain 3 — Incident Response | Perform file system forensic analysis | 4 | `disk_analyzer` |
| case19 | Chain of Custody | Domain 3 — Incident Response | Apply evidence handling and chain of custody procedures | 3 | `coc_reference` |
| case20 | Containment | Domain 3 — Incident Response | Select and justify containment strategy | 4 | `containment_advisor` |
| case21 | Timeline | Domain 3 — Incident Response | Reconstruct incident timeline from multi-source evidence | 4 | `timeline_builder` |

**Difficulty distribution:**
- Diff 3: case14, case15, case17, case19 (4 cases)
- Diff 4: case16, case18, case20, case21 (4 cases)

**XP values:**
- Diff 3: 150 XP
- Diff 4: 250 XP

---

## 3. Story Continuity

Stage 3 opens a new arc: **Project MERIDIAN**.

During Stage 2's forensic analysis of the NexusCorp breach, the Veridian IR team
discovered evidence of a second, dormant attacker — a low-and-slow APT that had
been present for weeks before the NexusCorp attacker made noise. The NexusCorp
attacker accidentally triggered detection; the APT was already there.

Stage 3 is the forensic investigation of the APT intrusion:

- **case14-15**: SIEM alerts started firing at unusual hours — triage the queue,
  identify which log sources are generating the signals
- **case16**: Threat hunt hypothesis — was the APT using living-off-the-land techniques?
- **case17-18**: Memory and disk forensics on the compromised host
- **case19**: Prepare evidence for potential legal proceedings — chain of custody
- **case20-21**: Contain the APT without tipping them off, reconstruct the full timeline

The APT is code-named **NIGHTWIRE**. Attribution: nation-state level, dwell time 6 weeks.

---

## 4. Dynamic Tools Design

### siem_correlator
- Input: pipe-delimited string — `RULES|||EVENTS`
  where RULES is newline-separated correlation rules in format:
  `RULE_ID:rule_name|CONDITION:field=value AND/OR field=value|SEVERITY:level`
  and EVENTS is newline-separated log events in format:
  `timestamp|source|event_type|field1=value1 field2=value2`
- Logic: evaluates each event against each rule's conditions; flags matches
- Output: alert table showing which rule triggered on which event, with severity

### log_classifier
- Input: newline-separated event descriptions (one per line)
- Logic: matches each event description against a hardcoded reference table of
  event types → log source mappings (e.g. "failed login" → "Windows Security Log / syslog auth")
- Output: table mapping each event type to its primary log source

### hunt_analyzer
- Input: pipe-delimited string — `HYPOTHESIS|||EVIDENCE`
  where HYPOTHESIS is a plain-text hunting hypothesis
  and EVIDENCE is newline-separated evidence items in format:
  `source:value` (e.g. `process:powershell.exe -enc`, `network:10.0.0.5:445`)
- Logic: scores each evidence item for how well it supports or refutes the hypothesis;
  searches embedded living-off-the-land (LOLBAS) reference for matching techniques
- Output: hypothesis assessment with supporting/refuting evidence and confidence score

### mem_analyzer
- Input: newline-separated memory artifact entries in format:
  `PID:N name:PROC base:0xADDR size:N permissions:rwx path:/path/or/[anon]`
- Logic: flags entries where:
  - permissions include execute AND path is `[anon]` or `/tmp/` → `[SUSPICIOUS]`
  - name matches known malicious process names → `[MALICIOUS]`
  - size is unusually large for the process type → `[ANOMALY]`
  - otherwise → `[OK]`
- Output: annotated memory map with flags and explanation

### disk_analyzer
- Input: newline-separated file system entries in format:
  `filename|size|created|modified|accessed|deleted:yes/no|path`
- Logic: flags entries where:
  - deleted=yes → `[DELETED]` (potential evidence of cleanup)
  - modified timestamp is BEFORE created timestamp → `[TIMESTOMPED]`
  - file is in `/tmp/`, `/dev/shm/`, or unusual path AND executable → `[SUSPICIOUS]`
  - filename matches known tool names (mimikatz, nc, ncat, meterpreter) → `[MALICIOUS]`
- Output: annotated file table with flags, sorted by suspicion level

### containment_advisor
- Input: pipe-delimited string —
  `asset:TYPE|threat:LEVEL|dwell:DAYS|data_sensitivity:LEVEL|attribution:KNOWN/UNKNOWN`
- Logic: evaluates containment options (full isolation, network isolation, monitoring-only,
  account lockout) against the scenario parameters; scores each option by effectiveness
  vs detection-tipping risk
- Output: ranked containment recommendation with rationale

### timeline_builder
- Input: newline-separated events in format:
  `timestamp|source|event_description`
- Logic: sorts events by timestamp, identifies gaps > 1 hour, groups events into
  IR phases (Preparation, Detection, Containment, Eradication, Recovery)
- Output: sorted chronological timeline with phase labels and gap annotations

### coc_reference (static)
- Returns the hardcoded chain of custody reference table
- Covers: evidence collection steps, documentation requirements, storage requirements,
  transfer procedures, and common chain of custody errors
- challenge_data ignored entirely

---

## 5. Engine Changes

All changes are **additive only** — no existing engine files modified except:

| File | Change |
|------|--------|
| `aegis/utils/tools.py` | Add 8 new tool functions + dispatch entries |
| `aegis/validate_content.py` | Add 8 new tools_type values to allowlist |
| `aegis/content/cases/` | Add case14-21.json |
| `aegis/content/registry.json` | Add case14-21 entries in order |
| `aegis/tests/test_tools_stage3.py` | Unit tests for all 7 new dynamic tools |

No engine changes (case_runner.py, main.py, save_manager.py unchanged).

---

## 6. Open Questions

- [x] Case count: 8 cases (case14-21) — Q1=C approved
- [x] Focus: Domain 1 SIEM/threat hunting + Domain 3 forensics — Q2=B approved
- [x] Difficulty: 3-4 throughout — Q3=A approved
- [x] Story: Project MERIDIAN — NIGHTWIRE APT forensic investigation
- [x] Domain 3 fully covered after Stage 3 (chain of custody, memory, disk, containment, timeline)

---

## 7. Out of Scope

- ❌ AEGIS Stage 4+ → future
- ❌ Engine refactor — case_runner.py unchanged
- ❌ Web UI → future
- ❌ Any CIPHER changes
- ❌ Domain 2 additions (fully covered in Stage 1+2)
- ❌ Domain 4 additions (fully covered in Stage 2)
