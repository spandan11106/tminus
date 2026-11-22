---
name: verify-pass
description: "Last step of every tminus command that emits facts or numbers. Recomputes every number with recompute.py, checks formulas and limits against the cited source pages, and ends the deliverable with a verification report. Use before declaring any pack, formula sheet, mock or cram pack done."
user-invocable: false
---

# Verify pass (always on, risk-based)

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.

## Always
1. **Every number.** Write each numeric result in the draft as a claim in `.tminus/claims-<doc>.json`:
   `{"id": "ex2-step3", "expr": "16*T/(pi*d**3)", "inputs": {"T": 1.2e6, "d": 40}, "claimed": 95.5,
   "source": "Ex 5.4, printed p. 152"}`. Use `"snippet"` (Python that sets `result`) for multi-step work and
   units as strings (`"10 kN"`) when they matter. Run
   `TM recompute .tminus/claims-<doc>.json --corrections progress/corrections_candidates.md`.
   Fix every MISMATCH in your draft. When the **book or slide** is wrong (not you), keep the correct value
   and add a `\flag{...}` (Markdown: **[FLAG]**) saying what the source prints, the correct value, and how you know.
2. **Every formula, limit, range and table value**: open the cited page (`pdftotext`) and compare. Watch for
   reversed limits (which end of a range applies to which case) and units.
3. **Printed answers**: where the book prints an answer, compare it with your recomputed value. A mismatch is
   either your error (fix it) or a book error (flag it), never ignored.
4. **Professor conventions**: check that every recipe and worked example follows them.

## Sample or skip
Descriptive prose: spot-check a few sentences against the source.

## Report
End the deliverable with a verification report (`tmverify` box, or a `## Verification report` section):
`Checked N | Matched N | Flagged N | Unverifiable N`, then one line per flag and per unverifiable item.
Anything you could not check is marked `[UNVERIFIED]` (`\unverified{...}`) in the body, never stated as fact.

## Independent check
If the command covers **more than 3 chapters** or produces a **mock paper**, also run the `verifier` subagent
(`@agent-tminus:verifier`) on the draft's claims with the source paths, without your reasoning, and resolve
every MISMATCH or NOT_FOUND it returns.
