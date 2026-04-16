# LESSONS_LEARNED.md — CyberForge
<!--
SCOPE: Every significant bug, design mistake, balance issue, and fix —
       with evidence. This file protects future contributors from
       repeating the same mistakes.
NOT HERE: Game logic → engine/
NOT HERE: Rules → CONSTITUTION.md

UPDATE: Continuously. Every significant issue gets an entry.
        Never delete entries — mark them resolved instead.

FORMAT: LL-[CATEGORY]-[NUMBER]: [Title]
-->

**Last updated:** 2026-04-09

---

## Categories

| Code | Meaning |
|------|---------|
| `ARCH` | Architecture / structural decisions |
| `GAME` | Gameplay / balance issues found in playtesting |
| `CODE` | Code bugs and fixes |
| `PLAN` | Planning / spec mistakes |
| `HINT` | Hint quality or escalation issues |
| `CERT` | Incorrect or outdated cert objective mappings |
| `CONTRIB` | Community contribution issues |

---

## When to Write a Lesson Learned

- Any bug that took >30 minutes to find
- Any operation/case that had to be redesigned after playtesting
- Any hint that players consistently got stuck on (balance issue)
- Any Python stdlib limitation that forced a workaround
- Any community PR that introduced a forbidden pattern
- Any cert objective that turned out to be wrong or outdated
- Any assumption about player behavior that proved incorrect

---

## Entry Template

```
### LL-[CAT]-[NUM]: [Short title]
**Date:** YYYY-MM-DD
**Status:** 🔴 Open | 🟡 In Progress | ✅ Resolved
**Discovered in:** [operation/case/module where it was found]
**What happened:** [What broke or went wrong — be specific]
**Why it happened:** [Root cause]
**Fix applied:** [What was changed and where]
**How to prevent:** [Rule or pattern to follow going forward]
**Added to CONSTITUTION?** Yes — §[section] | No
```

---

## Log

*(No entries yet — project just initialized.
Add entries here as issues are discovered during development.)*
