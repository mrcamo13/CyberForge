# plan.md — AEGIS Stage 2: Cases 06-13
<!--
SDD Phase 1 of 4: Plan
Next: spec.md → tasks.md → build
-->

**Module:** aegis-stage2
**Date:** 2026-04-12
**Depends on:** aegis-stage1 (cases 01-05, full engine)
**Adds to:** aegis/content/cases/, aegis/utils/tools.py, aegis/validate_content.py

---

## 1. What problem does this solve?

AEGIS Stage 1 covered the foundational SOC workflow across CySA+ Domains 1-3
at difficulty 1-3. Stage 2 expands to full exam coverage:

- **Deeper Domain 1-3 coverage** at difficulty 3-4: network traffic analysis,
  threat hunting, MITRE ATT&CK mapping, firewall rule gap analysis
- **Domain 4 (Reporting & Communication)** — the most-neglected exam domain:
  executive reporting, remediation prioritization, regulatory notification

Stage 2 also upgrades the tool tier from hardcoded simulators (Q3=A) to
**dynamic tools** (Q3=B): tools that actually parse structured input and
compute results from `challenge_data` rather than returning fixed output.

---

## 2. Cases Overview

8 cases: case06-case13. Difficulty resets to 2 for new topic areas
before ramping to 4 for capstone cases.

| Case | Title | Domain | Cert Objective | Difficulty | tools_type |
|------|-------|--------|---------------|------------|-----------|
| case06 | C2 Beaconing | Domain 1 — Security Ops | Analyze network traffic for C2 indicators | 2 | `traffic_analyzer` |
| case07 | IOC Hunt | Domain 1 — Security Ops | Correlate threat intel IOCs against log data | 2 | `ioc_hunter` |
| case08 | ATT&CK Mapping | Domain 1 — Security Ops | Map observed TTPs to MITRE ATT&CK | 3 | `attack_mapper` |
| case09 | Firewall Gap | Domain 2 — Vuln Mgmt | Identify rule gaps that permitted the attack | 3 | `rule_analyzer` |
| case10 | Risk Scoring | Domain 2 — Vuln Mgmt | Score risk using likelihood × impact matrix | 3 | `risk_scorer` |
| case11 | Exec Report | Domain 4 — Reporting | Translate technical finding to exec summary | 2 | `none` |
| case12 | Remediation Order | Domain 4 — Reporting | Prioritize remediation actions by impact | 4 | `remediation_planner` |
| case13 | Breach Notification | Domain 4 — Reporting | Determine regulatory notification requirements | 4 | `none` |

**Difficulty distribution:**
- Diff 2: case06, case07, case11 (3 cases — gentle intro to new topics)
- Diff 3: case08, case09, case10 (3 cases — intermediate)
- Diff 4: case12, case13 (2 cases — capstone)

**XP values:**
- Diff 2: 100 XP
- Diff 3: 150 XP
- Diff 4: 250 XP

---

## 3. Story Continuity

Stage 2 follows the NexusCorp incident into the post-eradication phase.
The analyst (player) is now part of the full IR and reporting cycle:

- **case06-07**: Post-incident threat hunt — was 10.0.0.99 beaconing to a C2?
  Were there other compromised hosts we missed?
- **case08-09**: Root cause analysis — map the attack chain to ATT&CK, identify
  the firewall rule gap that let the attacker in
- **case10**: Risk assessment — score the residual risk after patching
- **case11-13**: Reporting cycle — brief the CISO, prioritize remediation,
  determine if the breach requires regulatory notification

Every case is framed as a new SOC ticket in the Veridian Systems post-incident
review. The narrative arc closes the NexusCorp storyline.

---

## 4. Dynamic Tools Design (Q3=B)

Each new tool in Stage 2 parses its `challenge_data` input and computes
results dynamically rather than returning hardcoded output.

### traffic_analyzer
- Input: structured connection records (CSV-like: `timestamp,src_ip,dst_ip,port,bytes,interval`)
- Logic: flags connections where interval < 60s AND repeated to same external IP
  (beaconing pattern), or large outbound bytes to single destination (exfil)
- Output: annotated connection table with [BEACON], [EXFIL], [OK] flags

### ioc_hunter
- Input: pipe-delimited string — `IOC_LIST|||LOG_DATA`
  where IOC_LIST is comma-separated IP/domain/hash values
  and LOG_DATA is newline-separated log entries
- Logic: searches each log line for any IOC match
- Output: match report showing which IOCs appeared in which log entries

### attack_mapper
- Input: a behavior description string (e.g. "python3 SUID bit spawned root shell")
- Logic: searches an embedded ATT&CK technique reference table
  (≈20 techniques, key ones for CySA+) for keyword matches
- Output: matching technique(s) with ID, name, tactic, and mitigation

### rule_analyzer
- Input: pipe-delimited string — `RULES|||TRAFFIC`
  where RULES is newline-separated firewall rules (action src dst port)
  and TRAFFIC is newline-separated connection records
- Logic: evaluates each traffic entry against rules in order (first match wins)
- Output: table showing each connection with the matching rule and action (ALLOW/DENY)

### risk_scorer
- Input: pipe-delimited string — `likelihood:N|impact:N|asset:TYPE|exploited:yes/no`
  where likelihood and impact are 1-5
- Logic: computes risk = likelihood × impact, maps to LOW/MEDIUM/HIGH/CRITICAL,
  adjusts for asset type and whether actively exploited
- Output: risk matrix with score, rating, and recommended response timeframe

### remediation_planner
- Input: newline-separated remediation items in format:
  `ACTION|EFFORT:N|IMPACT:N|DEPENDENCY:ID_or_none`
  where effort and impact are 1-5
- Logic: ranks items by impact/effort ratio (quick wins first),
  respects dependency ordering
- Output: ranked remediation plan with priority and rationale

---

## 5. Engine Changes

All changes are **additive only** — no existing files modified except:

| File | Change |
|------|--------|
| `aegis/utils/tools.py` | Add 4 new tool functions + dispatch entries |
| `aegis/validate_content.py` | Add 4 new tools_type values to allowlist |
| `aegis/content/cases/` | Add case06-13.json |
| `aegis/content/registry.json` | Add case06-13 entries |

No engine changes (case_runner.py, main.py, save_manager.py unchanged).

---

## 6. Open Questions

- [x] Case count: 8 cases (case06-13) — Q1=C approved
- [x] Difficulty: reset to 2-4 — Q2=B approved
- [x] Tools: dynamic (parse input, compute results) — Q3=B approved
- [x] Story: NexusCorp post-incident arc closes in case13
- [x] Domain 4 included: cases 11, 12, 13

---

## 7. Out of Scope

- ❌ AEGIS Stage 3+ → future
- ❌ Engine refactor — case_runner.py unchanged
- ❌ Web UI → Stage 4
- ❌ Any CIPHER changes
