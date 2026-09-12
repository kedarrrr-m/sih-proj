# 🗺️ BUILD MAP — SIH 2026 · Adaptive Path Planning & Collision Avoidance (MathWorks, PS 26037)

Generated from **Project Bible v5** + `bridge_starter.py`. Every technical decision below traces to a specific part of the bible; nothing is invented. Where the bible marks a decision **Open** (Appendix C), it appears as an explicit *gating token* rather than a guessed answer.

---

## 1. Strategic Overview

You already own the **perception pillar** (FusionSegNet, a zero-annotation confidence-fusion segmenter); the problem statement is scored on **planning + collision avoidance**, which is currently Gap 1. This build closes that gap by growing the shipped `bridge_starter.py` scaffold — fake-perception → BEV cost map (EDT + uncertainty) → A* → replan-on-hazard — into a real closed loop where FusionSegNet feeds the cost map, a non-holonomic Hybrid A* plans over it, and three adaptive-caution signals (perception **uncertainty** = Idea B, **occlusion** phantoms = Idea C, agent **behaviour** margins = Idea A) make the word "adaptive" visible on screen. The default stack is **Python (PythonRobotics + CARLA/SUMO or a 2D BEV fallback)** per the bible's decision rule for a team without an ADT license, with a MATLAB/RoadRunner port as an additive sponsor-points bonus. The ultimate deliverable is a demoable, metricised loop (CARLA Driving Score + NHTSA scenarios) plus the **domain-gap result** (nuScenes→IDD) that converts your biggest vulnerability into a headline finding.

**Critical path:** Phase 0 → **Phase 2 (the loop)** is make-or-break. Phase 1 (perception numbers) and Phase 2 (planner) can run **in parallel** from Day 0 because the starter script provides a fake upstream — this parallelism is the whole point of Part VII-C.

---

## 2. Phase Breakdown

---

### PHASE 0 — Lock the Story & Stand Up Infrastructure
**Phase Objective:** Every unforced-error risk (R2, R4) is closed, all Appendix-C decisions blocking the build are resolved and dated, the repo/env is reproducible, and `bridge_starter.py` runs on every teammate's machine — so parallel work can begin.

- **`T0.1` — Verify PS ID on the official portal**
  - **Action:** Confirm whether the statement is **26037** or **26038** on the official SIH portal (Bible §1.1, R2). Record the verified number and date in Appendix C.
  - **Dependencies:** None.
  - **Validation:** A single verified PS ID is written in Appendix C with a date; no document still shows both.
  - **Complexity:** Low.

- **`T0.2` — Resolve the "from scratch" claim (Gap 3)**
  - **Action:** Decide Option A (keep ImageNet-pretrained EfficientNet-B0, correct the writeup to "fine-tuned end-to-end, early stages frozen; decoder/ASPP/attention/fusion-labelling ours") per Bible §Gap-3, and confirm whether SIH rules actually forbid pretrained weights (Appendix C open Q1). Edit the FusionSegNet writeup cell to match code.
  - **Dependencies:** None.
  - **Validation:** Writeup text and the architecture cell agree; a judge reading both finds no contradiction. Decision logged in Appendix C.
  - **Complexity:** Low.

- **`T0.3` — Select ideas & name the system**
  - **Action:** Lock the Part VI selection — **Build B + C + G, Stretch A, Slide-only D/E/F** — and choose the system name (`[[NAME]]`, Appendix C). Log both.
  - **Dependencies:** None.
  - **Validation:** Appendix C rows "Which ideas" and "System name" are no longer Open.
  - **Complexity:** Low.

- **`T0.4` — Lock the stack & sim decision**
  - **Action:** Per Bible VII-B.5 decision rule, choose planner path (**Hybrid A*** global + reactive local) and sim target (**PythonRobotics + CARLA/SUMO** default, or **2D BEV fallback** if compute is tight; MATLAB port deferred to Phase 3). Log in Appendix C.
  - **Dependencies:** T0.3.
  - **Validation:** Appendix C "Planner" and "Sim" rows resolved with a one-line rationale each.
  - **Complexity:** Low.

- **`T0.5` — Repo, environment & role assignment**
  - **Action:** Create the git repo, pin a `requirements.txt` (`numpy, scipy, matplotlib` minimum; add `shapely, opencv-python` for later phases), and assign Part XIII workstream owners (fill the `[[ ]]` role table).
  - **Dependencies:** None.
  - **Validation:** Fresh clone + `pip install -r requirements.txt` succeeds on a second machine; role table has no blank owners.
  - **Complexity:** Low.

- **`T0.6` — [PHASE GATE / TEST] Reproduce the baseline artifact**
  - **Action:** Every teammate runs `python3 bridge_starter.py` and regenerates `bridge_demo.png`; diff visually against the shipped reference (Bible VII-C).
  - **Dependencies:** T0.5.
  - **Validation:** Script exits 0 on all machines, prints a non-null initial path length and a "replanned OK" line, and the produced PNG matches the shipped one (road corridor, cost map, original+replanned paths). **Phase 0 is done only when the loop runs everywhere.**
  - **Complexity:** Low.

---

### PHASE 1 — Perception Solid + Domain-Gap Result
**Phase Objective:** FusionSegNet has honest, reproducible numbers on both domains, the **domain-gap experiment (Idea G)** table is filled, and the signature confidence-map visual exists. *(Runs in parallel with Phase 2.)*

- **`T1.1` — Finish nuScenes training + baseline/ablation numbers**
  - **Action:** Complete training on nuScenes v1.0-mini; produce mIoU, per-class IoU (Road/Sidewalk/Vehicle/Human), binary drivable-space IoU, FPS/params/size, and the ablation over confidence-weighting / temporal loss / TTA / copy-paste / SE+attention (Bible §Part IX, §4).
  - **Dependencies:** T0.2 (writeup fixed first).
  - **Validation:** All numbers regenerate from the notebook end-to-end with no placeholders; checkpoint saved to Drive (R10).
  - **Complexity:** Medium.

- **`T1.2` — Establish the nuScenes↔IDD↔5-class label remap**
  - **Action:** Build the label-mapping table (Appendix C open row) so IDD's hierarchy collapses to the FusionSegNet 5-class scheme, and pin the standard IDD split (6991/1912/957, Bible §2.2 / Appendix B).
  - **Dependencies:** None.
  - **Validation:** Remap applied to a handful of IDD frames produces visually correct 5-class masks; the class level you report is stated explicitly.
  - **Complexity:** Medium.

- **`T1.3` — Run the domain-gap experiment (Idea G)**
  - **Action:** Evaluate the nuScenes-trained model on IDD-val **before** adaptation; record nuScenes-val vs IDD-val mIoU and the Δ (Bible §2.2 table).
  - **Dependencies:** T1.1, T1.2.
  - **Validation:** The "gap" row is a real measured number, presented next to IndiVNet's 69.98% as *context, not like-for-like* (comparability caveat stated).
  - **Complexity:** Medium.

- **`T1.4` — IDD fine-tuning / domain adaptation (recovery)**
  - **Action:** Fine-tune/adapt to IDD; fill the "recovery" column and, if available, the IDD-AW rain/fog/night subset number.
  - **Dependencies:** T1.3.
  - **Validation:** Recovery column filled with real numbers; IDD-val mIoU improves measurably vs T1.3 or the honest result is reported as-is (R8 — it's a result, not a failure).
  - **Complexity:** Medium.

- **`T1.5` — Confidence-map demo visual + TorchScript export**
  - **Action:** Produce the per-pixel confidence-map visualisation (the signature slide) and export the model to TorchScript/ONNX for the bridge (Bible §4.5, §14.3).
  - **Dependencies:** T1.1.
  - **Validation:** Confidence map renders on an IDD clip; TorchScript module loads and runs a forward pass outside the notebook.
  - **Complexity:** Medium.

- **`T1.6` — [PHASE GATE / TEST] Perception integration check**
  - **Action:** Run the full eval harness (5-view TTA eval + FPS) and assemble the §2.2 domain-gap table and KPI perception fields end-to-end.
  - **Dependencies:** T1.3, T1.4, T1.5.
  - **Validation:** Every perception KPI (mIoU, per-class, drivable IoU, IDD gap+recovery, FPS) reproduces from a clean run with zero `[[placeholders]]`; matches Integrity Checklist (Part XVI).
  - **Complexity:** Medium.

---

### PHASE 2 — Close the Loop (Make-or-Break)
**Phase Objective:** The MVP loop of §3.2 runs on *real* perception: FusionSegNet mask+confidence → BEV EDT cost map with the uncertainty term → non-holonomic Hybrid A* → constant-velocity prediction → reactive avoidance/emergency stop → **visible replan on hazard**, looping in sim. This retires the #1 risk (R1).

- **`T2.1` — SWAP 1: real FusionSegNet output into the bridge**
  - **Action:** Replace `make_fake_perception()` with the TorchScript FusionSegNet mask + confidence (after IPM to BEV), preserving the `(GRID_H, GRID_W)` shapes (`bridge_starter.py:51`, Bible VII-C SWAP 1).
  - **Dependencies:** T1.5, T0.6.
  - **Validation:** `seg_to_occupancy` + `build_cost_map` run unchanged on real arrays; cost map renders with finite drivable region.
  - **Complexity:** Medium.

- **`T2.2` — Harden the BEV cost map (EDT + uncertainty, Idea B)**
  - **Action:** Confirm/extend `build_cost_map()` — EDT obstacle inflation, vehicle-radius hard block, and `uncertainty_weight*(1-conf)` term — and tune weights against §7.1. Keep the `extra_cost` hook for SWAP 3.
  - **Dependencies:** T2.1.
  - **Validation:** Low-confidence cells demonstrably raise cost; A* routes around a synthetic low-confidence patch (Idea B visible). No knife-edge hugging of obstacles.
  - **Complexity:** Medium.

- **`T2.3` — SWAP 2: PythonRobotics Hybrid A* global planner**
  - **Action:** Replace the toy 8-connected `astar()` with `hybrid_a_star_planning(start, goal, ox, oy, xy_res, yaw_res)`; derive `ox/oy` obstacle lists from the cost grid; add steering penalty + max-steering constraint (Bible §7.3, VII-B.5, SWAP 2).
  - **Dependencies:** T2.2.
  - **Validation:** Planner returns a *car-like* (non-holonomic) path with bounded turning radius on the real cost map; degenerate-narrow-corridor failure is caught and reported (mentionable limitation, VII-B.1).
  - **Complexity:** High.

- **`T2.4` — Constant-velocity prediction + reactive avoidance/emergency stop**
  - **Action:** Add constant-velocity/constant-turn-rate extrapolation of tracked agents, a TTC check, and the `CRUISE→YIELD→SLOW→EMERGENCY_STOP→REPLAN` fail-safe fallback (Bible §7.2, §7.4).
  - **Dependencies:** T2.3.
  - **Validation:** When no safe trajectory exists in the horizon, the system executes a controlled stop (provable fallback); TTC triggers at the expected distance on a scripted approach.
  - **Complexity:** High.

- **`T2.5` — Adaptive replan loop in sim (continuous-cost `replanPath` analogue)**
  - **Action:** Generalise `drive_and_replan()` into a continuous loop in the chosen sim (2D BEV fallback or CARLA/SUMO), injecting the scripted pedestrian-from-behind-parked-car hazard and replanning on graded cost (Bible VII-C step 5, VII-B.2 novelty).
  - **Dependencies:** T2.4, T0.4.
  - **Validation:** Ego drives the path, hazard appears within look-ahead, cost is raised, and the path **visibly replans** (not just once — the loop keeps stepping). Mirrors §3.2 items 4–5.
  - **Complexity:** High.

- **`T2.6` — [PHASE GATE / TEST] Full MVP loop end-to-end**
  - **Action:** Run perception→costmap→predict→plan→check→control as a continuous loop on one Indian (IDD) clip + one scripted hazard; capture the replan/stop event.
  - **Dependencies:** T2.5.
  - **Validation:** The five §3.2 MVP criteria all pass in one run: real perception → BEV cost map → trajectory on drivable space → visible replan-or-stop → runs in a loop. **R1 is retired.** Capture a screen recording as evidence.
  - **Complexity:** High.

---

### PHASE 3 — Adaptive Layers, Metrics & (Optional) MATLAB Port
**Phase Objective:** The loop demonstrably adapts caution to **three** signals (confidence, occlusion, behaviour), the full Part IX metric suite + NHTSA scenario battery produce reportable numbers, and — if time — the loop is ported to MATLAB/RoadRunner for sponsor points.

- **`T3.1` — SWAP 3a: Occlusion-aware phantom agents (Idea C)**
  - **Action:** Ray-cast occluded regions in the BEV grid, place a worst-case phantom agent in each, and feed the resulting cost via the `extra_cost` hook so the ego slows pre-emptively (Bible §7.4, Idea C, SWAP 3).
  - **Dependencies:** T2.6.
  - **Validation:** Approaching a parked bus, the ego **slows before the pedestrian is visible**, then the pedestrian appears (the phantom demo beat, §14.2).
  - **Complexity:** Medium.

- **`T3.2` — SWAP 3b: Behaviour-aware safety margins (Idea A, stretch)**
  - **Action:** Classify each tracked agent cautious/normal/aggressive from short-history features (speed variance, lateral deviation, heading-change rate, gap-acceptance — thresholds first, no graph theory) and inflate that agent's footprint proportionally via `extra_cost` (Bible Idea A). *Build only if tracking works and time remains (Bible: stretch).*
  - **Dependencies:** T3.1 (and a working tracker).
  - **Validation:** Two identical scenes differ only in one agent's aggression → planner gives the erratic agent a visibly wider berth (§14.2 beat 3).
  - **Complexity:** High.

- **`T3.3` — Scenario suite + planning/avoidance metrics**
  - **Action:** Script the NHTSA-typology scenarios (pedestrian/cyclist, unsignalled intersection, jaywalker, wrong-way auto, animal) under clear/rain/fog/night; compute collision rate, success rate, min TTC, hard-brake count, smoothness (curvature/jerk), replanning latency, and the speed-vs-confidence / speed-vs-occlusion adaptivity plots (Bible §Part IX).
  - **Dependencies:** T3.1.
  - **Validation:** Per-scenario table populated with real numbers; adaptivity plots show caution rising with low confidence and high occlusion (proof of "adaptive").
  - **Complexity:** High.

- **`T3.4` — Composite CARLA Driving Score**
  - **Action:** Compute **Route Completion × Infraction Penalty** across the scenario set; report Route Completion and Driving Score separately (Bible §Part IX).
  - **Dependencies:** T3.3.
  - **Validation:** One composite Driving Score number plus Route Completion is reproducible from the logged runs.
  - **Complexity:** Medium.

- **`T3.5` — MATLAB/RoadRunner port (optional, sponsor points)**
  - **Action:** *If* ADT access exists and time allows (timebox to 2 days, R6), port the cost map into `vehicleCostmap` → `inflationCollisionChecker` → `validatorVehicleCostmap` → `plannerHybridAStar`, and reproduce the replan loop via the Lane-Level Path Planning cosim, extending stock binary `replanPath` to continuous cost (Bible VII-B.1/VII-B.2). Skip cleanly if the bridge eats the timebox.
  - **Dependencies:** T2.6; T0.4 decision.
  - **Validation:** Either a working RoadRunner replan demo exists, **or** the token is explicitly de-scoped in Appendix C with the Python loop remaining the primary demo (R6 mitigation honoured).
  - **Complexity:** High.

- **`T3.6` — [PHASE GATE / TEST] Adaptivity + metrics verification**
  - **Action:** Run the full scenario battery once more, confirm all three adaptive signals fire, and freeze the Part IX numbers into the KPI slide.
  - **Dependencies:** T3.3, T3.4 (T3.2/T3.5 if built).
  - **Validation:** KPI slide fields all filled (Driving Score · Route Completion · 0 collisions across N scenarios · X FPS · Y ms replan · IDD mIoU); every metric measured on stated hardware, none estimated (Part XVI).
  - **Complexity:** Medium.

---

### PHASE 4 — Pitch, Demo & Freeze
**Phase Objective:** A rehearsed <4-min pitch with a recorded fallback demo, a clean deck, a passed integrity checklist, and frozen code — submission-ready.

- **`T4.1` — Record the demo video**
  - **Action:** Capture the §14.2 run-of-show: Indian clip → segmentation → confidence map → cost map forming → hazard replan → occlusion slow-down → (aggressive-agent berth) → numbers. Pre-record to defuse demo-laptop risk (R7).
  - **Dependencies:** T3.6.
  - **Validation:** Video matches exactly what the code does (Part XVI); the 2D BEV fallback demo also runs live as backup.
  - **Complexity:** Medium.

- **`T4.2` — Build the deck**
  - **Action:** Assemble slides around the five memorability points (§14.3): confidence-map visual, zero-annotation labelling, visible caution, the measured domain-gap result, MathWorks-native framing; add the frugal-deployment slide (Idea F) and future-work slide (Ideas D/E).
  - **Dependencies:** T3.6, T1.6.
  - **Validation:** Deck contains the domain-gap table and KPI slide with no `[[placeholders]]`; 30-second pitch (§14.1) fits.
  - **Complexity:** Low.

- **`T4.3` — Rehearse the Q&A drill**
  - **Action:** Drill all Part XV questions, especially "where's the planning?", "why nuScenes for India?", "pretrained weights?", "isn't this the RoadRunner example?", and "what doesn't work yet?" (name two real limitations honestly).
  - **Dependencies:** T4.2.
  - **Validation:** Every team member can answer each Part XV question in one breath; the novelty sentence (continuous-adaptive cost vs binary block) is delivered verbatim.
  - **Complexity:** Low.

- **`T4.4` — [PHASE GATE / TEST] Integrity checklist + code freeze**
  - **Action:** Walk the entire Part XVI integrity checklist; run `grep -r "\[\[" ` across all docs to confirm no placeholders remain; tag the frozen commit.
  - **Dependencies:** T4.1, T4.2, T4.3.
  - **Validation:** Every Part XVI box ticked (PS ID verified, writeup↔code consistent, licences cited, metrics reproducible, demo matches code, no placeholders); repo tagged and frozen. **Submission-ready.**
  - **Complexity:** Low.

---

## 3. Dependency Spine (Critical Path)

`T0.1–T0.6` → **`T2.1 → T2.2 → T2.3 → T2.4 → T2.5 → T2.6`** → `T3.1 → T3.3 → T3.4 → T3.6` → `T4.*`

Phase 1 (`T1.*`) runs **in parallel** off `T0.6`, feeding `T2.1` (via T1.5) and the deck. Stretch tokens `T3.2` and `T3.5` are **additive** — droppable without breaking the spine (R5/R6).
