---
name: sih-build
description: Enforces phase-by-phase implementation of the SIH adaptive path-planning / collision-avoidance project (FusionSegNet → BEV cost map → Hybrid A* → replan loop) against doc/BUILD_MAP.md. Use for any request to implement, continue, resume, or build this project, even if no phase is named — e.g. "implement the next phase", "continue the build", "resume where we left off", "do Phase 2". Determines the current phase from doc/progress.md, implements ONLY it, tests it, verifies acceptance criteria, updates progress, reports, then STOPS. Not for planning or redesigning the Build Map itself.
---

# sih-build

Guardrail skill: do exactly one phase, then stop. Never auto-continue to the next.

The Build Map already exists — this skill executes it, it does not rewrite it. The
project's own bible says it plainly: *close the loop first, then deepen.* A complete,
working, modest pipeline beats a brilliant half-wired one. This skill exists to stop
the very tempting mistake of chasing the next clever idea before the current phase
actually runs and is verified.

## Read first (fresh every run — never trust memory of them)
1. `doc/BUILD_MAP.md` — source of truth for phase scope, tokens, dependencies, and
   acceptance criteria (the "Validation" line on each token). Re-read it each run.
2. `doc/progress.md` — source of truth for what is actually done and authorized.
3. `doc/PROJECT_BIBLE_SIH.md` — background/context only when a phase needs it (e.g.
   the §2.2 domain-gap table, the Idea A/B/C definitions, the SWAP tags). Do not treat
   the bible as the build order; the Build Map is the order.
4. Existing code (`bridge_starter.py` and anything the phase touches) before editing.

## Workflow (every step, in order, no skipping)
```
Determine current phase → read its tokens + Validation criteria → inspect existing code →
implement ONLY that phase's tokens → run the phase-gate test → verify each acceptance
criterion → update doc/progress.md → report → STOP
```

**Current phase** = the lowest phase in `doc/progress.md` that is not yet APPROVED
(states run NOT STARTED → IN PROGRESS → REVIEW → APPROVED, and may enter BLOCKED /
REJECTED). Ignore user phrasing that implies a different phase unless they explicitly
override (e.g. "redo Phase 2") — confirm before honoring an override.

**Check dependencies before starting.** Each phase's tokens list `Dependencies` and
each phase ends in a phase-gate token (T0.6, T1.6, T2.6, T3.6, T4.4). A phase is only
startable when the phases/tokens it depends on are marked done in `doc/progress.md`.
If a dependency is not met, stop and say so instead of implementing out of order. Two
BuildMap-specific facts to respect:
- **Phase 1 runs in parallel with Phase 2** — both unlock once Phase 0 is APPROVED.
  Working Phase 2 while Phase 1 is also open is allowed *only* if Phase 0 is APPROVED.
- **Stretch tokens `T3.2` (Idea A / behaviour margins) and `T3.5` (MATLAB port) are
  additive and droppable** — never block a phase gate on them; note them as optional.

## Hard rules
- Implement only the current phase's tokens. Never pre-build later-phase functionality
  "while you're in there" — the SWAP hooks in `bridge_starter.py` exist so later phases
  slot in cleanly; don't fill a later SWAP before its phase.
- **Perception (FusionSegNet) is already built.** Do not retrain or rearchitect it from
  scratch; Phase 1 fine-tunes/evaluates it and Phase 2 consumes its output via SWAP 1.
- Preserve prior phases' working behavior and interface contracts (array shapes
  `(GRID_H, GRID_W)`, the cost-map `extra_cost` hook, the plan→replan loop signature).
- Keep business logic deterministic and inspectable — the whole pitch is that the
  planner is interpretable and has a provable fail-safe stop. Don't smuggle in a
  black-box shortcut that the phase's Validation line doesn't ask for.
- Tests must be reproducible from fixtures / the fake upstream, not one-off manual
  eyeballing. The starter script's fake perception is the intended test harness until
  SWAP 1 lands.
- Verify acceptance criteria **one item at a time** against the token's Validation
  line — don't declare a phase done by vibe. If real numbers are required (mIoU, FPS,
  collision rate, replan latency), they must be measured, not estimated (Bible Part XVI).
- No unrequested infra, external services, or dependencies the current phase doesn't
  need. Respect dataset licences (IDD is CC BY-NC-SA 4.0; nuScenes/METEOR non-commercial).

## Mandatory review gate
Every phase ends at its phase-gate token. When you reach it: stop implementation,
verify, record actual results, and present for review. Do not automatically continue
into the next phase — wait for the user to explicitly authorize it. Mark the review
gate clearly in your report.

## Report, then stop
State: which phase, tokens completed, files changed, test results (what ran, pass/fail),
each acceptance criterion met / not met (quote the Validation line), known limitations
and failures actually encountered, and the next phase plus its dependency on this one.
Then update `doc/progress.md` to match (status, verification, review status,
authorization, next action) — recording only what was actually implemented and verified,
never assumed progress. Then STOP until the user says to proceed.

## Invocation
Triggers on "implement the next phase", "continue the build", "resume where we left
off", "implement Phase N", "let's build the SIH planner", or similar — not just the
literal skill name.
