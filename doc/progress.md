# Build Progress

## Purpose

This document tracks execution progress against the project's BuildMap.

It does **not** define phases, phase objectives, implementation scope, or acceptance criteria.

The BuildMap is the sole source of truth for what each phase contains.

This document only records:

* Current execution state
* Phase progression
* Implementation status
* Verification status
* Review gates
* Authorization to proceed
* Relevant execution notes

---

# Current Status

* **Current phase:** Phase 1 — Perception Solid + Domain-Gap Result (started under explicit user override; see note)
* **Phase status:** Phase 0 IN PROGRESS (T0.3 name + T0.5 roles **deferred by user**); Phase 1 IN PROGRESS (T1.2 tooling done; T1.1/T1.3/T1.4/T1.5/T1.6 blocked on external assets)
* **Implementation started:** Yes
* **Review status:** PENDING
* **Next phase authorized:** Phase 1 started per explicit user instruction (2026-09-12), overriding the "Phase 0 APPROVED first" gate. Phase 0 not formally APPROVED — T0.3 (system name) and T0.5 (role table) deferred by the user; T0.2 notebook edit still pending.

> Source of truth: [`BUILD_MAP.md`](BUILD_MAP.md) (in this `doc/` directory). The BuildMap defines 5 phases (Phase 0–Phase 4). Execution begins with Phase 0.

---

# Phase Progress

| Phase                                                   | Status      | Review  | Authorized to Proceed |
| ------------------------------------------------------- | ----------- | ------- | --------------------- |
| Phase 0 — Lock the Story & Stand Up Infrastructure      | In Progress | Pending | No                    |
| Phase 1 — Perception Solid + Domain-Gap Result          | In Progress | Pending | No                    |
| Phase 2 — Close the Loop (Make-or-Break)                | Not Started | Pending | No                    |
| Phase 3 — Adaptive Layers, Metrics & (Optional) MATLAB Port | Not Started | Pending | No                |
| Phase 4 — Pitch, Demo & Freeze                          | Not Started | Pending | No                    |

> The number and names of phases must be taken from the project's BuildMap. Do not invent, redefine, or duplicate phase information here.

---

# Execution State Model

Each phase progresses through these states:

**NOT STARTED → IN PROGRESS → REVIEW → APPROVED**

A phase may also enter:

**BLOCKED** or **REJECTED**

### NOT STARTED

No implementation work for the phase has begun.

### IN PROGRESS

Implementation for the phase is actively being performed.

### REVIEW

Implementation is complete enough to evaluate against the BuildMap requirements.

Testing and verification results must be recorded before requesting approval.

### APPROVED

The phase has passed review and the user has explicitly authorized progression.

### BLOCKED

Progress cannot continue because of an unresolved dependency, failure, or external constraint.

### REJECTED

The phase was reviewed but requires changes before it can be approved.

---

# Progress Rules

## 1. BuildMap is authoritative

The BuildMap defines:

* Phase names
* Phase objectives
* Phase scope
* Phase dependencies
* Phase acceptance criteria
* Phase-specific requirements

Do not duplicate this information here.

---

## 2. Never assume progress

Only work that has actually been implemented and verified may be recorded as progress.

Never infer completion from:

* Existing files
* Partial implementation
* Previous conversations
* Intended functionality
* Planned work
* Code that has not been tested
* A later phase appearing to depend on it

---

## 3. Sequential progression

Phases are executed according to the dependency/order defined by the BuildMap.

A phase cannot be marked **APPROVED** merely because its implementation exists.

It must first pass verification and review.

---

## 4. Mandatory review gate

At the end of each phase:

1. Stop implementation.
2. Verify the work completed.
3. Record actual verification results.
4. Record failures and limitations.
5. Present the phase for review.
6. Wait for explicit authorization.
7. Only then begin the next authorized phase.

Do not automatically continue after verification.

---

## 5. No future-phase leakage

While executing a phase:

* Do not implement unrelated future-phase functionality.
* Do not mark future work as completed.
* Do not modify future-phase status based on partial dependencies.
* If future work becomes necessary, record it as a dependency or note.

---

# Phase Progress Record

For every phase currently being executed, maintain only execution information. No phase has begun; all records below are seeded from the BuildMap in the NOT STARTED state.

### Phase 0 — Lock the Story & Stand Up Infrastructure

**Status:** IN PROGRESS
**Implementation started:** Yes (2026-09-12)

**Implementation status (per token):**
- **T0.1 — Verify PS ID — DONE & VERIFIED.** PS ID = **26037**, verified against the official SIH-2026 community dataset (NoBugNinja repo, scraped 2026-08-22). 26038 is a different PS (Diabetic Retinopathy). Recorded in Appendix C; the "shows both" ambiguity was cleared from the bible top-banner, §1.1, and the BuildMap title.
- **T0.2 — "From scratch" claim (Gap 3) — PARTIAL / BLOCKED.** Verified PS 26037 contains **no** pretrained-weights prohibition (open Q1 answered: self-imposed). Option A recommended and logged. Not complete: the writeup edit lives in the FusionSegNet notebook, which is **not in this repo** (on Drive), and the team has not formally ratified Option A.
- **T0.3 — Ideas + name — PARTIAL.** Ideas **RESOLVED → B + C + G, stretch A** (Appendix C). System **name still OPEN** (team's creative choice; `[[NAME]]` unfilled) → Validation not fully met.
- **T0.4 — Stack + sim — DONE.** Planner = Hybrid A* global + reactive local; Sim = **PythonRobotics + CARLA/SUMO** (2D BEV fallback). Logged in Appendix C with rationale + the PS-26037 MATLAB-leaning caveat.
- **T0.5 — Repo/env/roles — PARTIAL.** Git repo exists; `requirements.txt` pinned; `bridge_starter.py` + `bridge_demo_reference.png` brought into the repo; `.venv` created and `pip install -r requirements.txt` verified (numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2). Not complete: Part XIII **role table still has blank owners** (needs real teammate names).
- **T0.6 — [PHASE GATE] Reproduce baseline artifact — DONE & VERIFIED (this machine).** `python bridge_starter.py` → exit 0, initial path length 112 cells, "replan triggered at step 40 (replanned OK)", replanned length 72 cells; regenerated `bridge_demo.png` is structurally identical to the shipped reference (3 panels: BEV semantic map, EDT+uncertainty cost map, plan→replan). Not verifiable by me: "runs on *every* teammate's machine" — the pinned venv + requirements.txt is the reproducibility mechanism.

**Verification:**
- T0.1: cross-checked official community dataset record for IDs 26035–26039.
- T0.5: `pip install -r requirements.txt` succeeded in a fresh `.venv`.
- T0.6: script exit code 0; stdout assertions (path length non-null, "replanned OK") present; output PNG visually matches reference.

**Failures / issues:** None encountered in the mechanical work. Blockers are missing human inputs, not failures.

**Known limitations:**
- T0.2 notebook edit cannot be done from this repo (FusionSegNet notebook is external/Drive).
- T0.6 verified on one machine only.

**Review status:** PENDING
**Authorization:** NOT AUTHORIZED

**Blocked on user (to close Phase 0):**
1. Ratify **Option A** for the pretrained-weights claim (T0.2), and edit the FusionSegNet notebook writeup cell (external to this repo).
2. Choose the **system name** (T0.3 / `[[NAME]]`).
3. Provide **teammate names** for the Part XIII role table (T0.5).

**Next action:** Present Phase 0 for review. Do NOT start Phase 1 or Phase 2 until the user resolves the three blockers above and explicitly authorizes progression. (Per BuildMap, Phase 1 ∥ Phase 2 both unlock only once Phase 0 is APPROVED.)

---

### Phase 1 — Perception Solid + Domain-Gap Result

**Status:** IN PROGRESS
**Implementation started:** Yes (2026-09-12, per explicit user instruction to start Phase 1 and skip T0.3/T0.5)

**Implementation status (per token):**
- **T1.2 — nuScenes↔IDD↔5-class label remap — DONE & VERIFIED (logic).** Implemented `perception/label_remap.py`: IDD level-3 label-name → 5-class map (drivable-fallback→ROAD, autorickshaw→VEHICLE, person/rider→HUMAN, etc.), a nuScenes-general → 5-class map, vectorised `remap_id_array`, and the pinned IDD split (6991/1912/957). Class level reported explicitly = **IDD level-3 names**. 6/6 fixture tests pass (`tests/test_label_remap.py`). **Not fully closed:** the "applied to a handful of real IDD frames → visually correct masks" half of the Validation needs the IDD dataset, which is not in this repo.
- **T1.1 — nuScenes training + baseline/ablation — BLOCKED.** Requires the FusionSegNet notebook (`FusionSegNet_v5.ipynb`), weights (`best_fusionsegnet_v5.pth`), the nuScenes v1.0-mini dataset, `torch`, and GPU — none present in this repo (they live in Colab/Drive). Producing mIoU/ablation numbers here would mean fabricating them, which the build skill forbids.
- **T1.3 — Domain-gap experiment — BLOCKED.** Depends on T1.1 (trained model) + IDD-val data. Not runnable here.
- **T1.4 — IDD fine-tuning — BLOCKED.** Depends on T1.3 + IDD data + GPU.
- **T1.5 — Confidence-map visual + TorchScript export — BLOCKED.** Depends on T1.1 (trained model) + torch.
- **T1.6 — [PHASE GATE] Perception integration check — BLOCKED.** Depends on T1.3/T1.4/T1.5; cannot run until the above are unblocked.

**Prerequisite tooling staged (unblocks T1.1/T1.3/T1.6 the moment assets arrive):** `perception/metrics.py` (mIoU / per-class IoU / drivable-space IoU from real masks), `perception/domain_gap.py` (§2.2 table assembler with IndiVNet caveat, takes measured inputs — invents nothing), `requirements-perception.txt` (torch/nuscenes-devkit/… for Colab), `perception/README.md` (drop-in eval cell for FusionSegNet_v5.ipynb).

**Verification:** `tests/test_label_remap.py` → 6 passed; `tests/test_metrics.py` → 5 passed. **11/11, exit 0.** (Deterministic fixtures; no dataset, no torch.)

**Failures / issues:** None in the mechanical work. The blocked tokens are missing external assets, not failures.

**Known limitations:**
- The label remap is verified on synthetic label arrays only; real IDD-frame validation is pending the dataset.
- IDD level-3 label *names* are used as the mapping key; when wiring to real data, supply the IDD devkit's `{id: name}` table to `build_id_lut` and confirm names match that devkit version.

**Review status:** PENDING
**Authorization:** NOT AUTHORIZED for Phase 1 completion.

**Blocked on user / external assets (to advance Phase 1):**
1. The FusionSegNet notebook + weights, and access to nuScenes v1.0-mini and IDD/IDD-val, in an environment with `torch` + GPU (Colab). Then T1.1 → T1.3 → T1.4 → T1.5 → T1.6 can run and produce the real §2.2 domain-gap table.
2. (Carried from Phase 0) T0.2 writeup edit in that same notebook; T0.3 system name; T0.5 teammate names.

**Next action:** Present Phase 1 for review. T1.2 tooling is ready to consume real data; the rest of Phase 1 is blocked on the notebook + datasets + GPU. Do NOT fabricate perception numbers. STOP for user direction.

---

### Phase 2 — Close the Loop (Make-or-Break)

**Status:** NOT STARTED
**Implementation started:** No
**Implementation status:** None.
**Verification:** None.
**Failures / issues:** None.
**Known limitations:** None.
**Review status:** PENDING
**Authorization:** NOT AUTHORIZED
**Next action:** Locked until Phase 0 is APPROVED (needs T1.5 output via SWAP 1). Critical path. Phase gate is T2.6 (full MVP loop; retires R1).

---

### Phase 3 — Adaptive Layers, Metrics & (Optional) MATLAB Port

**Status:** NOT STARTED
**Implementation started:** No
**Implementation status:** None.
**Verification:** None.
**Failures / issues:** None.
**Known limitations:** None.
**Review status:** PENDING
**Authorization:** NOT AUTHORIZED
**Next action:** Locked until Phase 2 is APPROVED. Tokens T3.2 (Idea A) and T3.5 (MATLAB port) are additive/droppable. Phase gate is T3.6.

---

### Phase 4 — Pitch, Demo & Freeze

**Status:** NOT STARTED
**Implementation started:** No
**Implementation status:** None.
**Verification:** None.
**Failures / issues:** None.
**Known limitations:** None.
**Review status:** PENDING
**Authorization:** NOT AUTHORIZED
**Next action:** Locked until Phase 3 is APPROVED. Phase gate is T4.4 (integrity checklist + code freeze; submission-ready).

---

# Review Gate Record

When a phase reaches review:

### Phase [X] Review

**Implementation:** Complete / Incomplete

**Verification:** Passed / Failed / Partial

**Issues remaining:**
[Actual unresolved issues]

**Acceptance status:** Passed / Failed / Partial

**User decision:**
Pending / Approved / Rejected

**Next phase authorization:**
Locked until explicit approval

---

# Update Rules

When progress changes, update the existing status rather than creating conflicting states.

The progress document must always answer:

1. **Where are we?**
2. **What has actually been implemented?**
3. **What has actually been verified?**
4. **Is review required?**
5. **Has the user approved progression?**
6. **What is currently authorized?**

Do not include historical progress unless it is necessary to understand the current state.

---

# Initial State

At the beginning of any new project:

**Current phase:** Not Started
**Implementation:** Not Started
**Verification:** Not Started
**Review:** Not Applicable
**Authorization:** None

All project phases begin as **NOT STARTED** and **NOT AUTHORIZED**.

The phase list itself must be populated from the project's BuildMap.
\