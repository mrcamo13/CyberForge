# plan.md — AEGIS Stage 4: Cases 22-31
<!--
SDD Phase 1 of 4: Plan
Next: spec.md
-->

**Module:** aegis-stage4
**Date:** 2026-04-15
**Status:** Draft

---

## Planning Answers

| Question | Answer |
|----------|--------|
| Q1 — Case count | C — 10 cases (case22-31) |
| Q2 — Domain split | B — Even: 5 Domain 2 (Vulnerability Management) + 5 Domain 4 (Reporting & Communication) |
| Q3 — Difficulty | A — Mix 3-4 |

---

## Why Stage 4

Stage 3 completed Domain 1 (Security Operations) and Domain 3 (Incident Response). Domains 2
and 4 together account for 45% of the CySA+ CS0-003 exam but have only 6 cases in the current
build — not enough depth. Stage 4 closes that gap and brings the simulator to near-complete
CySA+ coverage.

**After Stage 4:** All 4 domains covered, 31 total cases, playable end-to-end for exam prep.

---

## CySA+ Objectives Targeted

### Domain 2 — Vulnerability Management (22% of exam)

Objectives not yet covered (or covered only lightly):

| Objective | Current State | Stage 4 Plan |
|-----------|--------------|--------------|
| 2.2: Analyze scan results using contextual factors (asset criticality, exploit availability, patch status) | Light (case03 CVSS only) | case22 — vuln_prioritizer |
| 2.3a: Identify inhibitors to remediation (business/operational constraints) | Not covered | case23 — patch_reference (static) |
| 2.4: Reduce attack surface (unnecessary services, exposure) | Not covered | case24 — surface_analyzer |
| 2.4: Software assurance / SAST output interpretation | Not covered | case25 — sast_analyzer |
| 2.3b: Threat intelligence integration with vulnerability prioritization | Not covered | case26 — intel_correlator |

### Domain 4 — Reporting & Communication (23% of exam)

Objectives not yet covered:

| Objective | Current State | Stage 4 Plan |
|-----------|--------------|--------------|
| 4.1: Security metrics — MTTD, MTTR, patch compliance rate | Not covered | case27 — metrics_calculator |
| 4.1: Compliance gap analysis and control mapping | Not covered | case28 — compliance_mapper |
| 4.1: SLA tracking and adherence reporting | Not covered | case29 — sla_tracker |
| 4.2: Post-incident lessons learned / root cause analysis | Not covered | case30 — lessons_reference (static) |
| 4.1: Executive vs. operational reporting — right metric, right audience | Partially (case11) | case31 — dashboard_filter |

---

## Story Arc — Operation IRONCLAD

Stage 3 ended with NIGHTWIRE contained and Project MERIDIAN formally opened. Stage 4 picks up
4 weeks later: the incident is closed, the post-incident report is filed, and Veridian Systems'
CISO has launched **Operation IRONCLAD** — a comprehensive program to remediate the
vulnerabilities NIGHTWIRE exploited, demonstrate compliance to the board, and build a mature
security metrics practice so the next threat is caught earlier.

The player is promoted from SOC analyst to **Vulnerability Management and Reporting Analyst**
— the person responsible for translating technical findings into business decisions and
demonstrating security posture improvement over time.

---

## Case Map

### Domain 2 — Vulnerability Management (case22-26)

| Case | Title | Tool | Difficulty | XP |
|------|-------|------|------------|-----|
| case22 | Vuln Triage | vuln_prioritizer | 3 | 150 |
| case23 | Patch Inhibitors | patch_reference | 3 | 150 |
| case24 | Attack Surface | surface_analyzer | 4 | 250 |
| case25 | Code Review | sast_analyzer | 4 | 250 |
| case26 | Threat Intel Vulns | intel_correlator | 3 | 150 |

### Domain 4 — Reporting & Communication (case27-31)

| Case | Title | Tool | Difficulty | XP |
|------|-------|------|------------|-----|
| case27 | Security Metrics | metrics_calculator | 3 | 150 |
| case28 | Compliance Gap | compliance_mapper | 4 | 250 |
| case29 | SLA Tracking | sla_tracker | 3 | 150 |
| case30 | Lessons Learned | lessons_reference | 3 | 150 |
| case31 | Executive Report | dashboard_filter | 4 | 250 |

**Totals:** 5 diff-3 × 150 XP = 750 + 5 diff-4 × 250 XP = 1250 → **2000 XP available in Stage 4**

---

## New Tool Functions (8 total: 6 dynamic + 2 static)

| tools_type | Type | Purpose |
|-----------|------|---------|
| `vuln_prioritizer` | Dynamic | Score and rank vulnerabilities using CVSS + contextual factors (asset criticality, exploit availability, patch availability) |
| `patch_reference` | Static | Hardcoded patch management reference: inhibitors, exceptions, compensating controls |
| `surface_analyzer` | Dynamic | Parse asset/service inventory, flag unnecessary exposure by attack surface category |
| `sast_analyzer` | Dynamic | Parse SAST tool output lines, classify by severity and CWE, identify top finding |
| `intel_correlator` | Dynamic | Match CVEs against threat intel (exploited in wild, PoC available, APT-linked), reprioritize remediation order |
| `metrics_calculator` | Dynamic | Compute MTTD, MTTR, patch compliance rate from raw incident/patch data |
| `compliance_mapper` | Dynamic | Map implemented controls against NIST CSF categories, compute gap percentage |
| `sla_tracker` | Dynamic | Parse incident tickets with timestamps and SLA targets, flag breaches, compute adherence rate |
| `lessons_reference` | Static | Hardcoded post-incident lessons learned structure and root cause categories |
| `dashboard_filter` | Dynamic | Given a mixed metric set, classify each metric as executive-appropriate or operational-only |

---

## Pre-Planning Checklist

- [x] Stage 3 complete (case14-21, 82 tests passing, validate_content clean)
- [x] Domain 2 gap identified: 5 cases covering objectives 2.2, 2.3, 2.4
- [x] Domain 4 gap identified: 5 cases covering objectives 4.1, 4.2
- [x] Story arc defined: Operation IRONCLAD, post-NIGHTWIRE
- [x] Difficulty distribution: 3,3,4,4,3 / 3,4,3,3,4 (five diff-3, five diff-4)
- [x] All 6 dynamic tools have clear, deterministic parsing contracts
- [x] 2 static reference tools follow exec_reference/coc_reference pattern

---

## Open Questions for Spec

1. **vuln_prioritizer input format:** CVSS score + contextual flags (internet_facing, exploit_available, patch_available, asset_criticality). Pipe or newline separated?
2. **compliance_mapper framework:** NIST CSF (5 functions) or ISO 27001 (Annex A domains)? NIST CSF is more common on CySA+ exam — propose NIST CSF.
3. **intel_correlator tie-break:** When two CVEs are both "exploited in wild," how to order? Propose: CVSS score as tie-break.
4. **dashboard_filter classification rules:** What makes a metric "executive" vs "operational"? Propose: executive = outcome-focused (risk reduction, compliance %, breach cost); operational = process-focused (scan count, alert volume, patch cycle time).
