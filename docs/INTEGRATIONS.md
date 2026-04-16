# INTEGRATIONS.md — CyberForge
<!--
SCOPE: Every external tool and URL referenced in hints across all
       operations and cases. The game makes NO calls to these —
       they are educational pointers only.
NOT HERE: Game logic → engine/
NOT HERE: Save schemas → docs/DATA_MODEL.md
NOT HERE: Rules → CONSTITUTION.md

UPDATE: Every time a new operation or case is added that references
        a new external tool, add it here before merging the PR.
-->

**Last updated:** 2026-04-09

---

## 1. Tools Referenced in Hints

These are the real-world tools players are directed to in Hint 1.
The game does NOT call these — they are learning pointers only.
All tools listed here must be free and require no login to use.

### Cryptography & Encoding

| Tool | URL | Used In | What Players Do There |
|------|-----|---------|----------------------|
| CyberChef | https://gchq.github.io/CyberChef/ | CIPHER op01, op02 | Caesar cipher decode, Base64 decode |

### Password & Hash Analysis

| Tool | URL | Used In | What Players Do There |
|------|-----|---------|----------------------|
| CrackStation | https://crackstation.net | CIPHER op05 | MD5 hash lookup via rainbow table |

### Vulnerability & CVE Research

| Tool | URL | Used In | What Players Do There |
|------|-----|---------|----------------------|
| NVD NIST | https://nvd.nist.gov | AEGIS case01, case02 | CVE lookup, CVSS score reading |
| MITRE CVE | https://cve.mitre.org | AEGIS case02 | CVE ID verification and description |

### Threat Intelligence & Attack Frameworks

| Tool | URL | Used In | What Players Do There |
|------|-----|---------|----------------------|
| MITRE ATT&CK | https://attack.mitre.org | AEGIS case06 | Technique and tactic mapping |

### Security Frameworks & Controls

| Tool | URL | Used In | What Players Do There |
|------|-----|---------|----------------------|
| NIST CSF | https://www.nist.gov/cyberframework | AEGIS case07 | Framework function and category reference |
| CIS Controls | https://www.cisecurity.org/controls | AEGIS case07 | Control mapping and gap analysis |
| NIST IR Lifecycle | https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf | AEGIS case05 | IR phase reference |

### Practice Platforms (Debrief next_step only)

These are referenced in debrief `next_step` fields — not in hints.
They point players to real tool practice after completing a simulation.

| Platform | URL | What Players Practice There |
|----------|-----|----------------------------|
| TryHackMe | https://tryhackme.com | Real tool labs aligned to each operation/case |
| HackTheBox | https://hackthebox.com | Unguided real machine exploitation |

---

## 2. Rules for Adding New Tool References

Before adding a new external URL to any hint or debrief:

- [ ] Tool is free — no paid account required to use it
- [ ] Tool requires no login to access the relevant feature
- [ ] URL is stable — prefer official domain over third-party mirrors
- [ ] URL has been verified to work as of the PR submission date
- [ ] Tool is added to this file before the PR is merged
- [ ] Navigation steps in the hint are exact and tested

---

## 3. Future Integrations (Post-MVP Only)

These are NOT active. Spec separately before implementing.

| Integration | Purpose | Constraint |
|-------------|---------|------------|
| NVD CVE API | Live CVE data for future content updates | Free tier, 5 req/30s without API key |
| Flask | Web UI for Stage 4 | Adds external dependency — spec first |

---

## 4. What CyberForge Does NOT Integrate With

- No analytics or telemetry services
- No authentication providers
- No cloud storage
- No LLM APIs at runtime
- No package registries (no pip calls)
