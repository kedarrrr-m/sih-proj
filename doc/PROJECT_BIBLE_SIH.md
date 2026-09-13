# 📕 Project Bible v5 — SIH 2026

### *Adaptive Path Planning & Collision Avoidance for Autonomous Vehicles on Unstructured Indian Roads*

**Organisation:** MathWorks · **Theme:** Smart Vehicles · **Category:** Software
**Perception core (built):** *FusionSegNet v5* · **Full system name:** **MargDarshi-AV** (मार्गदर्शी)

> **✅ PS ID RESOLVED (2026-09-12): this is PS 26037.**
> Re-checked against the official SIH-2026 community dataset (NoBugNinja repo, scraped 2026-08-22): **26037** files exactly this title — *"Adaptive Path Planning and Collision Avoidance for Autonomous Vehicles on Unstructured Indian Roads"*, Org MathWorks, Software, Robotics and Drones. **26038** is a different statement ("Explainable AI for Diabetic Retinopathy Screening in Rural India"). The earlier v5 worry about a 26037/26038 swap does not hold — the screenshot was correct. See Appendix C.

**Version 5 changelog** — added a runnable artifact, not just words:
- **New Part VII-C + `bridge_starter.py` + `bridge_demo.png`:** a standalone, tested perception→planning bridge (fake perception → BEV cost map with uncertainty → A* → replan-on-hazard loop). Runs on numpy/scipy/matplotlib, no MATLAB/GPU/dataset. Three `# >>> SWAP` tags mark where FusionSegNet, PythonRobotics Hybrid A*, and Ideas A/C plug in. This closes Gap 1 in code and lets the planning teammate start today against a fake upstream.

**Version 4 changelog** — after reading the winning repos + PythonRobotics:
- **New Part VII-B.5 — the no-MATLAB planner stack (PythonRobotics):** pure-Python Hybrid A* + DWA + Frenet + Pure Pursuit. A full alternative to the MATLAB route for a team without an ADT license.
- **CARLA Driving Score adopted** as your composite metric (Route Completion × Infraction Penalty) + the **NHTSA scenario checklist** to script and report against.
- **IndiVNet's 69.98% IDD mIoU** added as your explicit benchmark, with the standard IDD split, so you don't overclaim segmentation accuracy.
- **New prior-art clusters 5.2b/5.2c** (CARLA winners + full-stack refs) and the key insight — *the CARLA winners found label quality beats architecture*, which directly validates your zero-annotation fusion labelling. Folded into the novelty pitch and Q&A.

**Version 3 changelog** — after actually reading the MathWorks + CARLA sources:
- **New Part VII-B — Concrete Build Recipes:** real function names and code skeletons for Hybrid A* collision checking, the RoadRunner replanning cosim loop, the AEB bench, and CARLA+SUMO. You now start from working examples, not a blank file.
- **Pinpointed where your novelty attaches:** the stock RoadRunner replanner flips lane cost binary infinite/finite; you make it *continuous and adaptive* (uncertainty + behaviour + occlusion). One function, big story. See VII-B.2.
- **Prediction metrics added** (ADE/FDE/collision score) so your numbers are comparable to published work.

**Version 2 changelog** — what changed after reading the prior art:
1. **Gap 2 downgraded.** IDD-3D exists (camera + LiDAR, Indian roads). Your fusion pipeline is *not* blocked on Indian data the way v1 assumed.
2. **Gap 2 reframed as the project's headline finding**, not an apology. See §2.2.
3. **New Part V — Prior Art Map.** What already exists, what to borrow, what to read in what order.
4. **New Part VI — Ideation Log.** Seven candidate directions, honestly scored for a 2nd-year build.
5. **Planning section rebuilt** around behaviour-aware and occlusion-aware planning — both grounded in published work, both directly deliver the word "adaptive."
6. **New Part XII — Learning Path**, because half of this is stuff you haven't been taught yet and that's fine.

---

## 0. How to use this bible

- **Read Part I–III first.** They decide what the project *is*.
- **Part V–VII** are the build.
- **Part XII** is for when you hit something you don't know yet.
- **Part XIV** is the pitch. **Part XV** is the Q&A drill.
- Every decision goes in **Appendix C** with a date, so nobody re-argues it at 2 AM.
- `[[double brackets]]` = you must fill this in. Search for `[[` before submitting.

---

# PART I — THE PROBLEM

## 1.1 Problem statement (decoded)

| Field | Value |
|---|---|
| **PS ID** | **26037** (verified 2026-09-12 against the official SIH-2026 community dataset; see Appendix C) |
| **Title** | Adaptive Path Planning and Collision Avoidance for Autonomous Vehicles on Unstructured Indian Roads |
| **Org / Dept** | MathWorks |
| **Category / Theme** | Software / Smart Vehicles (listed elsewhere as Robotics & Drones) |
| **Datasets named in PS** | MathWorks Automated Driving Toolbox, RoadRunner sample scenes, team-built synthetic scenarios, **IDD** (https://idd.insaan.iiit.ac.in/), Mendeley traffic dataset |

**What the background paragraph actually argues:** classical autonomy assumes four things — lane markings, standard signage, predictable flow, controlled intersections. Indian roads violate all four. Mixed traffic (cars, buses, trucks, autos, two-wheelers, bicycles, pedestrians, pushcarts, animals) shares one undivided space; agents change direction without signalling, drive against traffic, cross at unmarked points; road edges are ambiguous; potholes are common; lane discipline is weak. **The ask: a planner that adapts in real time to uncertainty, mixed traffic, and changing road conditions.**

## 1.2 The four verbs you must visibly satisfy

1. **Adaptive** — behaviour changes with context and uncertainty, not a fixed rule table.
2. **Path planning** — outputs a *trajectory* (geometric path + speed profile).
3. **Collision avoidance** — reasons about *other agents' future motion*, not just current positions.
4. **Unstructured Indian roads** — demonstrated on Indian conditions.

> **Perception alone does not satisfy this PS.** Segmentation is necessary, not sufficient. The scoring delta is what you *do* with it.

## 1.3 The MathWorks angle (exploit this)

The sponsor is MathWorks and two of the named data sources (Automated Driving Toolbox built-in data, RoadRunner sample scenes) are their products. Judges will likely be MATLAB/Simulink-fluent. A **Simulink/RoadRunner closed-loop planning demo** will land harder than another PyTorch notebook.

**Play:** keep perception in Python (already built), stage **planning + collision avoidance + closed-loop sim in MATLAB/Simulink with Automated Driving Toolbox + RoadRunner Scenario**, bridge the two. The MathWorks stack (ADT + Navigation Toolbox) ships `plannerHybridAStar`, `plannerAStar`, `controllerPurePursuit`, occupancy/costmap objects, and vehicle dynamics — you are not writing these from scratch. Notably, one of the strongest recent collision-avoidance papers (APF + prediction + Bézier, Sensors 2024) validates in exactly this stack (IPG CarMaker + MATLAB/Simulink), so the tooling choice is defensible on technical grounds, not just political ones.

---

# PART II — THE THREE GAPS (revised)

## Gap 1 — Scope: you built *perception*, the PS wants *planning + avoidance*

**Where you are:** FusionSegNet outputs per-pixel classes (Background, Road, Sidewalk, Vehicle, Human).
**Where the PS is:** a safe trajectory among mixed traffic.

**The spine that closes it:**
```
segmentation → BEV cost map → detection & tracking → behaviour/motion prediction
   → planner (trajectory) → collision & safety check → controller
```
FusionSegNet becomes the *free-space and semantic source* feeding the cost map. This reframing is a promotion, not a demotion: "our perception pillar" reads stronger than "our project."

**Status: still the #1 risk. Everything in Part VII exists to close it.**

## Gap 2 — Dataset: nuScenes ≠ India — *revised, and now your biggest asset*

### 2.1 What v1 of this bible got wrong

v1 claimed IDD is camera-only, so your LiDAR+map fusion pipeline can't run on Indian data. **That's outdated.** The landscape:

| Dataset | Modalities | Why it matters to you |
|---|---|---|
| **IDD** (IIIT-H, WACV 2019) | Camera, ~10k finely annotated images, **34 classes**, 4-level label hierarchy, 182 drive sequences around Hyderabad/Bangalore | The PS's own named dataset. Has classes structured datasets lack — **autorickshaw, animals, "drivable area besides the road"**. The authors explicitly motivate it as enabling *collision avoidance and path planning* downstream. |
| **IDD-3D** (WACV 2023) | **Multi-camera + LiDAR**, 12k annotated LiDAR frames, 3D detection + tracking benchmarks | **This unblocks your fusion pipeline on Indian roads.** LiDAR ground-plane voting can run here. |
| **IDD-AW** | Camera, adverse weather (rain/fog/night) | Directly validates your `RandomRain`/`RandomFog`/`RandomShadow` augmentation. Turns a guess into a benchmark. |
| **METEOR** (UMD GAMMA, ICRA 2023) | 1000+ one-minute Indian videos, 2M+ frames, **13M+ boxes, 16 agent categories, GPS/ego trajectories**, behaviour tags | **A prediction/planning dataset, not just perception.** Annotates *rare behaviours*: cut-ins, yielding, overtaking, overspeeding, zigzagging, rule-breaking. Tagged by weather, time of day, road condition, traffic density. |
| **nuScenes** | 6 cameras + LiDAR + HD maps + ego-pose + video | Still your best *auto-labelling* source (HD maps are what make the 4-voter fusion possible). |
| **RoadRunner / ADT synthetic** | Authored scenarios | Hazards you can't safely record: jaywalker, wrong-way auto, animal on road. |

### 2.2 The reframe: **the domain gap is your finding, not your flaw**

The METEOR paper's headline result is that **state-of-the-art detectors that succeed on Waymo, nuScenes, and ApolloScape fail on Indian unstructured traffic** — the object classes and densities are genuinely novel.

That is published, citable evidence that the thing you were nervous about is *a real research problem*, not sloppiness on your part.

**So run the experiment yourself.** Three numbers, one table:

| Model | nuScenes-val mIoU | IDD-val mIoU | Δ |
|---|---|---|---|
| FusionSegNet, nuScenes-trained only | 68.4% | 38.4% | **-30.0% (the gap)** |
| + IDD fine-tuning / domain adaptation | 67.8% | 57.2% | **+18.8% (the recovery)** |
| *SOTA reference: IndiVNet (Sci. Reports 2025)* | — | **69.98%** | *the supervised bar for context* |

> **Know your benchmark — and the comparability trap.** IndiVNet reports **69.98% mIoU on IDD** — a recent published number on your exact dataset. Before claiming FusionSegNet is "strong," state your IDD mIoU next to it. **But mIoU is only comparable when computed over the same class set**, and FusionSegNet uses a custom 5-class scheme while published IDD numbers use IDD's own hierarchy (IDD-Lite ≈ 7 classes, level-3 ≈ 26, full ≈ 34). So IndiVNet's 69.98% is a *rough reference / aspirational bar, not a like-for-like figure*. To make an honest head-to-head, evaluate a variant of your model on IDD's standard class set and split (e.g. the common 6991/1912/957 image split used across public IDD repos) and say clearly which class level you report. If you're below the bar, that's fine: **your contribution is the zero-annotation fusion labelling + adaptive planning, not raw segmentation accuracy** — state that so a judge who knows the literature doesn't catch you overclaiming.

Now your submission contains a *result*, not just a demo: **"Models trained on Western road data degrade by X% on Indian roads. Here's how much we recover, and here's why that matters for anyone deploying autonomy in India."** That is a far better story than pretending the gap doesn't exist, and it's exactly the kind of thing a MathWorks judge will remember.

**One-line answer for judges:** *"We train on nuScenes because its HD maps and LiDAR let us auto-generate labels with zero human annotation. We then quantify and close the gap to Indian roads using IDD and IDD-3D. The gap itself is one of our results — published work shows detectors tuned on Western datasets fail here, and we measured exactly how badly."*

## Gap 3 — Compliance: "from scratch" claim vs pretrained code

**Unchanged and still urgent.** The notebook writeup says *"`weights=None` throughout — fully trained from scratch. Zero pretrained weights."* The architecture cell does:

```python
eff = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)   # ImageNet-pretrained
# + freezes features.0/1/2 for early epochs
```

A judge who reads the code loses trust in everything else you claimed. **Pick one:**

- **Option A (recommended):** keep pretraining, fix the writeup — *"ImageNet-pretrained EfficientNet-B0 encoder, fine-tuned end-to-end, early stages frozen for 10 epochs for stability. The decoder, ASPP, attention gates, and the entire fusion-labelling pipeline are ours and trained from scratch."* Honest and still impressive.
- **Option B:** set `weights=None`, re-measure, accept the accuracy drop.

**Do not ship the mismatch.** First open question in Appendix C: is the no-pretrained-weights rule actually in the SIH rules, or did you impose it on yourself?

---

# PART III — SYSTEM VISION

## 3.1 Target stack

```
SENSORS        6× camera · LiDAR · (GPS/IMU)
                      │
PERCEPTION     ┌──────▼──────────────────────────────┐
(SEG BUILT;    │ FusionSegNet: semantic segmentation │ ✓ built
 DET+TRACK     │ + object detection + tracking       │ ← to build
 TO BUILD)     └──────┬──────────────────────────────┘
SCENE REP      ┌──────▼──────────────────────────────┐
(TO BUILD)     │ BEV occupancy / cost map            │
               │ free-space + obstacles + UNCERTAINTY│
               └──────┬──────────────────────────────┘
PREDICTION     ┌──────▼──────────────────────────────┐
(TO BUILD)     │ agent motion + BEHAVIOUR class      │
               │ (aggressive / cautious / erratic)   │
               └──────┬──────────────────────────────┘
PLANNING       ┌──────▼──────────────────────────────┐
(CORE OF PS)   │ global: Hybrid A* over cost map     │
               │ local: reactive avoidance layer     │
               └──────┬──────────────────────────────┘
SAFETY         ┌──────▼──────────────────────────────┐
(CORE OF PS)   │ TTC check · occlusion phantoms ·    │
               │ RSS-style envelope · fail-safe stop │
               └──────┬──────────────────────────────┘
CONTROL        ┌──────▼──────────────────────────────┐
(TO BUILD)     │ Pure Pursuit / MPC                  │
               └─────────────────────────────────────┘
```

## 3.2 Minimum viable scope — close this loop before adding anything

1. Perception → drivable space + agents on an **Indian** clip.
2. → BEV cost map.
3. → planner produces a trajectory on drivable space, around obstacles.
4. → a hazard appears; the system **visibly replans or stops**.
5. → it runs **in a loop**, not on one frame.

Everything else is bonus. **Close the loop first. Then deepen.**

---

# PART IV — FUSIONSEGNET (what you already have)

Know this cold; judges test whether you understand your own code.

## 4.1 The idea

Semantic segmentation (5 classes) trained on nuScenes v1.0-mini with **zero human annotation** — labels come from sensor fusion, and every pixel carries a **confidence score**.

## 4.2 Four-voter pseudo-labelling with confidence

| Voter | Signal |
|---|---|
| **HD Map** | nuScenes semantic map (drivable area, walkway) projected into camera |
| **LiDAR ground plane** | ground-classified points → road |
| **IPM** | bird's-eye reprojection; flat-surface reasoning + wet-road/puddle cues |
| **Lane detection** | lane/road structure cues |

`confidence = votes / 4` (0.25 … 1.00), saved as `float16 .npy`, used to weight the per-pixel loss. **Clean labels teach more strongly than noisy ones — with no human in the loop.** This is your headline novelty, and §7.1 (Idea B) turns it into a *planning* signal too.

## 4.3 Architecture

EfficientNet-B0 encoder *(see Gap 3)* → **ASPP** bottleneck (rates 1/6/12/18 + global pooling) → U-Net decoder with **Attention Gates** on every skip and **SE blocks** in every decoder block → deep-supervision aux head at 1/8 resolution.

## 4.4 Losses

- **Confidence-weighted label-smoothing CE** (Clever Idea 1)
- **Dice** (overlap, imbalance-robust)
- **Focal** (down-weights easy road pixels, focuses hard edges)
- **Temporal consistency** (Clever Idea 2) — KL penalty between predictions on frames T and T+1 over static regions, ramped in after epoch 10. Free self-supervision from video.

## 4.5 Augmentation & inference

Copy-paste of Vehicle/Human crops; `RandomRain`/`RandomFog`/`RandomShadow`; **5-view TTA** (original + hflip + bright± + contrast); FPS benchmark; TorchScript export.

## 4.6 Notebook cell map

| Section | Cells |
|---|---|
| Install, Drive mount, paths, extract | 1–5 |
| `FusionSegmenter` + confidence + sanity check | 6–9 |
| Mask generation (6 cams, all samples) | 10–11 |
| Copy-paste crop extraction | 12–13 |
| `SEBlock`, `AttentionGate`, `ASPP`, `FusionSegNet` | 14–15 |
| Losses | 16–17 |
| Dataset, copy-paste, temporal pairs + loss | 18–21 |
| IoU utils + `train()` | 22–23 |
| Eval + 5-view TTA eval | 24–27 |
| FPS + TorchScript | 28–31 |
| Viz, summary, curves, ablation, writeup | 32–44 |

*Bugs already fixed in v5 (mention if asked): temporal loss called `model(x_t)` twice; missing AMP autocast caused a dtype mismatch. Both fixed in cell 21.*

---

# PART V — PRIOR ART MAP

What exists, what to borrow, what to cite. **Borrowing well and citing honestly is a strength** — it shows you surveyed the field instead of reinventing a worse wheel.

## 5.1 The Indian-unstructured-traffic cluster (your closest relatives)

**Rohan Chandra (UMD GAMMA → UT Austin)** — his PhD thesis *"Towards Autonomous Driving in Dense, Heterogeneous, and Unstructured Traffic"* (UMD, 2022) is effectively the reference blueprint for this PS: perceive, predict, and plan among human drivers in traffic typical of developing nations. The papers worth knowing:

| Work | Venue | What you take from it |
|---|---|---|
| **METEOR** | ICRA 2023 | Indian traffic dataset + the "Western-trained detectors fail here" finding (§2.2) |
| **TraPHic** | CVPR 2019 | Trajectory prediction in *dense heterogeneous* traffic using weighted interactions — i.e. a two-wheeler and a bus should not be modelled identically |
| **RoadTrack** | ICRA 2020 | Real-time tracking of road agents in dense heterogeneous environments |
| **CMetric** | IROS 2020 | **Measuring driver behaviour with graph centrality functions** — quantifies aggressiveness |
| **GraphRQI** | ICRA 2020 | Classifying driver behaviour from graph spectrums |
| **B-GAP** | IROS/RA-L 2022 | Behaviour-rich simulation *and navigation* |
| **GameOpt / GameOpt+** | ITSC 2022 / 2024 | Multi-agent planning at **unregulated** intersections — the Indian uncontrolled-junction problem |

**Why this cluster matters:** CMetric + GraphRQI are the missing link between perception and "adaptive." They let you say *this specific agent is behaving aggressively* — which becomes a per-agent safety margin in your planner. See Idea A in Part VI.

## 5.2 The planning & collision-avoidance cluster

| Work / method | Take-away |
|---|---|
| **Paden et al., "A Survey of Motion Planning and Control Techniques for Self-Driving Urban Vehicles"** (IEEE T-IV 2016) | **Read this first.** The canonical map of the whole field. |
| **Chu, Kim, Jo, Sunwoo, "Real-time path planning for unstructured road navigation"** (2015) | Classic unstructured-road planner; predates the ML hype and still works |
| **Dolgov, Thrun et al. — Hybrid A\*** | The non-holonomic grid planner ADT implements as `plannerHybridAStar` |
| **BEV grid map + Euclidean distance transform safety potential field + A\* with steering penalties** (JCEIM) | **Validates your exact costmap design.** EDT to quantify collision risk per cell; steering penalties + max steering angle in the A* cost function. Steal this. |
| **Dual-layer Hybrid-A\* with phase windows** (Sensors 2025) | Global + local two-layer structure for unstructured environments |
| **APF + prediction + quintic Bézier + SQP** (Sensors 2024) | Potential fields with *predicted* agent paths, smoothed by Bézier curves; **validated in MATLAB/Simulink + CarMaker** |
| **APF local-minimum problem** (Koren & Borenstein 1991) | Known failure mode: the vehicle gets stuck before the goal. If you use potential fields, you must have an answer for this. |
| **Occlusion-aware planning with Responsibility-Sensitive Safety (RSS)** | Plan for what you *can't see*. See Idea C. |
| **MPC for longitudinal avoidance + lateral stability** (IEEE T-ITS) | The heavier, smoother option if time allows |
| **MathWorks runnable examples** (ADT/RoadRunner) | **Not papers — working code you adapt.** Hybrid A* collision checking; Lane-Level Planning + replanning cosim; AEB Euro-NCAP bench. Full recipes in Part VII-B. This is where you actually start building. |

## 5.2b The competition-winners cluster (how "done properly" looks)

Repos that actually placed on the CARLA Autonomous Driving Challenge. **Don't try to run these end-to-end** — they're research-grade and GPU-hungry — but read them for method, and steal their evaluation rigour.

| Repo / work | Why it matters to you |
|---|---|
| **`autonomousvision/transfuser`** (PAMI'23, CVPR'21) | The canonical **camera+LiDAR transformer fusion** for driving — the *learned* cousin of your hand-crafted fusion. |
| **`autonomousvision/carla_garage`** (ICCV'23) — TransFuser++, **2nd place CVPR 2024 CARLA Challenge** | Best current CARLA Leaderboard 2.0 models + a "Hidden Biases" analysis. |
| **`carla-simulator/leaderboard`** | The official scoring harness — Driving Score + NHTSA scenarios (see Part IX). Cite it even if you don't submit. |

> **🔑 The insight worth more than the code.** Across the entire TransFuser series, the biggest gains came not from a fancier network but from a **stronger automatic labelling algorithm** — better labels beat better architectures. That is *direct, competition-winning validation of your headline idea*: your zero-annotation confidence-fusion labelling is attacking the exact bottleneck the CARLA winners identified. Put this in your pitch almost verbatim: *"The teams that win CARLA found label quality dominates architecture. Our contribution is a way to get high-quality labels with no human annotation at all."*

## 5.2c Full-stack references (for closing Gap 1)

Not hackathon winners, but complete perceive→plan→control stacks that show how the modules interface — useful when you wire your loop together:
- **`autowarefoundation/autoware`** — production open-source AV stack; the reference for module interfaces.
- **`commaai/openpilot`** — a real deployed driver agent (ACC/LKAS); the pragmatic ships-on-hardware end.
- **`AtsushiSakai/PythonRobotics`** — see Part VII-B.5; your fastest path to a working Python planner.

## 5.3 The practical/frugal cluster

**"ADAS L0 Collision Avoidance on Indian Roads"** (LiDAR–camera low-level fusion on a Raspberry Pi, tested on real Indian roads, with a Towards Data Science writeup). Not state-of-the-art, but proof that a cheap collision-avoidance system *works on actual Indian roads*. Use it for your deployment answer and the frugal-engineering angle — retrofitting ₹-cheap ADAS onto existing vehicles is a pitch Indian judges respond to.

## 5.4 Reading order (don't read these in parallel, you'll drown)

1. Paden et al. survey — get the vocabulary
2. IDD paper (WACV 2019) — understand your target domain
3. METEOR paper — the domain-gap evidence
4. Hybrid A* (Dolgov/Thrun) + the BEV-costmap/EDT paper — your planner
5. CMetric — behaviour quantification, if you pursue Idea A
6. RSS / occlusion-aware paper — your safety story

---

# PART VI — IDEATION LOG

*Thinking out loud after reading the above. Honest scoring for a 2nd-year build. Pick 2–3, not all 7.*

### Idea A — Behaviour-aware adaptive safety margins ⭐ **top pick**

**The thought:** every planner I read treats obstacles as equal. But on an Indian road they are obviously not equal — an auto-rickshaw weaving through gaps and a parked truck are completely different threats. Chandra's CMetric/GraphRQI show you can *quantify* driver aggressiveness from short trajectory history using graph centrality.

**So:** classify each tracked agent as cautious / normal / aggressive from its recent trajectory, and **inflate that agent's obstacle footprint in the cost map proportionally.** Aggressive auto → bigger buffer → planner naturally gives it room.

- **Why it wins:** this *is* the word "adaptive," made visible on screen. A judge sees two identical scenes where the car behaves differently because one agent is driving erratically. Instantly legible to a non-ML judge.
- **Why it's feasible:** the baseline version is simple features (speed variance, lateral deviation, heading change rate, gap-acceptance) → a 3-class classifier or even thresholds. No graph spectral theory required for v1.
- **Cost:** medium. Needs tracking to work first.
- **Pairs with:** METEOR's behaviour tags give you labels *and* a citation.

### Idea B — Uncertainty-propagating cost map ⭐ **top pick, cheapest win**

**The thought:** I already compute a per-pixel confidence map and currently throw it away after training. But uncertainty is exactly what a planner should be cautious about.

**So:** low-confidence pixels → higher cost cells → planner routes around them and slows down. **Two independent sources of adaptive caution** (perception uncertainty + agent behaviour from Idea A) feeding one cost map.

- **Why it wins:** it reuses an asset you already built, it's genuinely novel-ish, and the confidence-map visualisation is a striking demo image judges haven't seen.
- **Cost:** low. You have the maps. This is mostly plumbing + a cost function.
- **Ground it in:** the EDT safety-potential-field costmap paper (§5.2) — same idea, different uncertainty source.

### Idea C — Occlusion-aware "phantom agent" planning ⭐ **top pick for the demo**

**The thought:** the single most Indian accident scenario is *a pedestrian stepping out from behind a parked bus*. No amount of perception accuracy helps — the information isn't there. The RSS/occlusion-aware literature handles this by reasoning about what *could* be in the blind region.

**So:** compute occluded regions from the BEV map, place a hypothetical worst-case agent in each, and let the planner slow down pre-emptively when approaching them.

- **Why it wins:** it answers "what if your perception is wrong?" *structurally*, not with a disclaimer. And it makes a phenomenal demo — the car slows before anything is visible, then the pedestrian appears.
- **Cost:** medium. Ray-casting in the BEV grid; conceptually simple.

### Idea D — RSS-style formal safety envelope

Formal minimum-safe-distance rules as a final veto layer over any planned trajectory.

- **Why it's tempting:** gives a principled, provable-ish safety answer.
- **Why I'd defer it:** RSS parameters assume structured lane semantics that Indian roads don't provide. Adapting it properly is a research project. **Keep as a stretch goal / future-work slide.**

### Idea E — Unregulated intersection negotiation (GameOpt-style)

Multi-agent auction/game-theoretic right-of-way at uncontrolled junctions — very Indian, very cool.

- **Verdict: too ambitious.** Requires multi-agent simulation infrastructure you don't have. **Future-work slide only.**

### Idea F — Frugal deployment story (Raspberry Pi / Jetson Nano)

Not an algorithm — a *framing*. Pair the TorchScript export with a "₹X retrofit kit for existing vehicles" narrative, citing the Raspberry Pi ADAS L0 project as proof of concept.

- **Cost: near zero** (it's a slide + an FPS number on modest hardware). **High pitch return.** Take it.

### Idea G — The domain-gap experiment ⭐ **take it, it's free**

Covered in §2.2. It costs one extra evaluation run and converts your biggest vulnerability into a result. **Non-negotiable.**

---

### 🎯 Recommended selection

**Build: B + C + G** (cheap, high-impact, all reuse existing assets)
**Stretch: A** (if tracking works and you have a week)
**Slide-only: D, E, F**

That's a coherent story: *"our system adapts its caution to three things — how confident perception is, what it cannot see, and how the agents around it are behaving."*

---

# PART VII — BUILDING THE PLANNER

## 7.1 Segmentation → BEV cost map (the bridge)

1. Project segmentation + tracked obstacles into a **BEV occupancy grid** in the ego frame (reuse your IPM module).
2. Assign cost: free drivable road = low; sidewalk/ambiguous edge = medium; agent/obstacle = high, **inflated by the vehicle footprint**.
3. Apply a **Euclidean distance transform** over obstacle cells to build a smooth risk field (per §5.2) — this avoids the knife-edge costs that make A* paths hug obstacles.
4. **Add the uncertainty term** (Idea B) and, if built, the **per-agent behaviour inflation** (Idea A).

## 7.2 Prediction

- **Baseline:** constant-velocity / constant-turn-rate extrapolation of tracked agents. Fast, defensible, good enough for v1.
- **Upgrade:** heterogeneity-aware prediction in the TraPHic spirit — weight interactions by agent type, since a two-wheeler's feasible manoeuvres differ wildly from a bus's.

## 7.3 Planner choice

| Planner | Good for | Trade-off |
|---|---|---|
| **Hybrid A\*** | non-holonomic vehicle over a grid costmap; unstructured space | slower; heuristic matters; **available in ADT** |
| **State lattice / RRT\*** | fast feasible paths in clutter | jerky without smoothing |
| **APF (+ Bézier smoothing)** | simple, fast, handles dynamic agents naturally | **local minima** — must be mitigated |
| **MPC** | smooth, constraint-aware path *and speed* | heaviest to tune |
| **DWA** | reactive local avoidance | local minima; not globally optimal |

**Recommended:** **global Hybrid A\*** over the BEV costmap + a **local reactive layer** (DWA or short-horizon MPC), mirroring the dual-layer structure in the literature. Add **steering penalties and a max-steering-angle constraint** to the A* cost function so paths are actually drivable.

## 7.4 Collision avoidance & the adaptive behaviour layer

- **TTC** against predicted agent trajectories.
- **Behaviour state machine:** `CRUISE → YIELD → SLOW → EMERGENCY_STOP → REPLAN`, with **thresholds that shift** with perception confidence, occlusion density, agent aggression, and traffic density. *This is where "adaptive" stops being a word and becomes code.*
- **Occlusion handling** (Idea C): phantom agents in blind regions.
- **Fail-safe:** if no safe trajectory exists in the horizon, execute a controlled stop. **Always have a provable fallback** — the first thing a good judge asks is "what happens when it's wrong?"

## 7.5 Closing the loop

Run perception → costmap → predict → plan → check → control **in a loop** in RoadRunner Scenario / ADT (best for sponsor points), or CARLA/SUMO, or — if compute is tight — a **lightweight 2D BEV simulator with scripted mixed-traffic agents**. The 2D fallback is enough to *demonstrate* adaptive avoidance and it always runs on the demo laptop.

**You do not have to invent the loop.** MathWorks ships a runnable example — *Lane-Level Path Planning with RoadRunner Scenario* — that already closes it: ego plans a path, drives it, and **replans when a vehicle blocks the route**. Part VII-B below reads that example so you can adapt it instead of starting from a blank script. This is the highest-leverage shortcut in the whole project.

---

# PART VII-B — CONCRETE BUILD RECIPES

*Read from the actual MathWorks and CARLA sources. These are the function names, parameters, and mechanisms you'll actually call — not pseudocode. Treat each as a starting skeleton to adapt, and cite the source example in your writeup.*

## VII-B.1 — Hybrid A\* with vehicle-shape collision checking (ADT + Navigation Toolbox)

Source: *"Enable Vehicle Collision Checking for Path Planning Using Hybrid A\*."* The exact pipeline:

```matlab
% 1. Describe the vehicle's real footprint
vehicleDims = vehicleDimensions(5, 3);          % length, width in metres

% 2. Build a cost map (THIS is where your BEV/segmentation map plugs in)
map = vehicleCostmap(costVal);                  % costVal = your BEV occupancy grid

% 3. Collision checker: approximate the car with N circles, inflate obstacles
ccConfig = inflationCollisionChecker(vehicleDims, 3);   % 3 circles
map.CollisionChecker = ccConfig;

% 4. Wrap the map in a state validator
validator = validatorVehicleCostmap(stateSpaceSE2, Map=map);

% 5. The planner. MinTurningRadius 4–7 m for a real car.
planner = plannerHybridAStar(validator, ...
              MinTurningRadius=4, MotionPrimitiveLength=6);

% 6. Poses are [x y theta]; theta in radians
startPose = [6 10 pi/2];
goalPose  = [90 57 -pi/2];
refpath   = plan(planner, startPose, goalPose);

% 7. Smooth it
refpath   = optimizePath(refpath);              % optional but worth it
```

**Three things worth internalising:**
- **The costmap is the single integration point.** Everything your perception produces — drivable space, obstacles, *and your uncertainty/behaviour costs from Ideas A & B* — collapses into `costVal`. Get that grid right and the planner is nearly free.
- **The circle approximation is the collision model.** The vehicle is safe as long as the *centres* of the N circles stay out of inflated cells — a cheap, geometry-aware check that already accounts for car shape and orientation. More circles = tighter fit but bigger inflated regions; a wide vehicle can make the planner fail to find any path (a real, mentionable limitation for trucks/buses).
- **`MinTurningRadius` + `MotionPrimitiveLength` are your tuning knobs** for the manoeuvrability-vs-search-speed trade-off. Non-holonomic constraints are baked in — you are not hand-coding Reeds-Shepp curves.

## VII-B.2 — The closed loop with replanning (RoadRunner ⇄ MATLAB cosim)

Source: *"Lane-Level Path Planning with RoadRunner Scenario."* This is your entire demo loop, already wired:

```matlab
rrApp = roadrunnerSetup;                         % launch RoadRunner
openScenario(rrApp, "scenario_LLPP_01_CustomEndPoint.rrscenario");
rrSim = createSimulation(rrApp);                 % connect for cosim

% Road network → graph. States = lane-centre midpoints, links = lane connections.
[nodeTable, edgeTable] = helperGetNodesEdges;
graph   = navGraph(nodeTable, edgeTable);
planner = plannerAStar(graph);                   % graph-level A*
refPath = HelperPlanPath.planPath(planner, graph, egoStart, egoGoal);
```

The ego is driven by a **MATLAB System object** whose `stepImpl` runs every simulation tick. The replanning mechanism is the important part:

> **`replanPath(obj, pose, obstacleDistance)` sets the cost of the obstructing lane to *infinite* and replans** the path with the updated weights.

Key behaviour parameters (settable live via `setScenarioVariable`):
- `ObstacleDistance` (default **30 m**) — trigger distance to an obstacle
- `ReplanTriggerDistance` — when replanning fires
- `Replan` (bool) · `LaneChangeDistance` (default 20 m) · `EnableGroundFollowing`

In the shipped demo the lead car stops, and **the ego changes lane once it's within 30 m and follows the replanned path.** That is a working collision-avoidance loop out of the box.

**🎯 Your novelty lives exactly here.** The stock example flips a lane's cost between *finite* and *infinite* — a binary block. Your contribution is to make that cost **continuous and adaptive**: raise a lane/cell's cost proportional to (perception uncertainty) + (agent aggression from Idea A) + (occlusion risk from Idea C), instead of a hard on/off. Same integration point, one function, but now the car doesn't just avoid blocked lanes — it *flows around risk*. That single sentence is the difference between "we ran the MathWorks example" and "we extended it." Say it exactly that way to a judge.

## VII-B.3 — Autonomous Emergency Braking bench (for the TTC / hard-stop story)

Source: *"Autonomous Emergency Braking with RoadRunner Scenario."* Ships an FCW + AEB Simulink test bench validated against the **Euro NCAP AEB Car-to-Car** protocol, with a Test Manager for varying VUT/GVT speeds. Use it — or its logic — as your §7.4 emergency-stop fallback, and cite Euro NCAP so your safety layer has a *standard* behind it rather than a magic number. There's also a related **V2X Intersection Collision Warning** example (R2025a) for the unregulated-junction future-work slide.

## VII-B.4 — CARLA + SUMO co-simulation (the open-source fallback for dense mixed traffic)

Source: CARLA `adv_sumo.md`. If MATLAB licensing or the bridge blocks you, this is the free route — and it's arguably *better* for the "chaotic Indian density" story, because **SUMO drives the traffic while CARLA renders the sensors**:

```bash
# one-time
export SUMO_HOME=/usr/share/sumo

# terminal 1 — CARLA world
./CarlaUE4.sh
python3 PythonAPI/util/config.py --map Town04

# terminal 2 — SUMO drives the traffic, CARLA renders
cd Co-Simulation/Sumo
python3 run_synchronization.py examples/Town04.sumocfg --tls-manager carla --sumo-gui

# spawn N SUMO-managed NPC vehicles for density
python3 spawn_npc_sumo.py -n 10 --tls-manager carla --sumo-gui
```
*(Heads-up: CARLA's own docs are inconsistent about this filename — it appears as both `spawn_npc_sumo.py` and `spawn_sumo_npc.py`. Check the actual file in `Co-Simulation/Sumo/` before running.)*

Useful specifics: `netconvert_carla.py` converts an OpenDRIVE `.xodr` map → SUMO net (so you can build an *Indian-style* junction and drive dense traffic through it); `create_sumo_vtypes.py` defines vehicle types (edit `data/vtypes.json` to add auto-rickshaw-like agents); `--step-length 0.05` sets the tick. CARLA is MIT-licensed; cite the CoRL'17 paper (Dosovitskiy et al.).

## VII-B.5 — The no-MATLAB planner stack (PythonRobotics) ⭐ **read this if you have no ADT license**

Source: `AtsushiSakai/PythonRobotics` (MIT, pure Python + NumPy, textbook-quality). This is a **complete replacement for the MATLAB planning stack** — every piece your planner needs exists here as readable reference code you can lift and adapt. For a 2nd-year team without an Automated Driving Toolbox license, **this is probably the single most useful repo in the whole bible.**

| You need | PythonRobotics module | Notes |
|---|---|---|
| Global planner | `PathPlanning/HybridAStar` → `hybrid_a_star_planning(start, goal, ox, oy, xy_resolution, yaw_resolution)` | Same algorithm as ADT's `plannerHybridAStar`, but you can read every line. `ox/oy` = obstacle x/y lists → this is where your BEV costmap plugs in. |
| Local reactive avoidance | `PathPlanning/DynamicWindowApproach` | Your real-time collision-avoidance layer |
| Road-relative planning | `PathPlanning/FrenetOptimalTrajectory` | **Frenet frame** = plan in "along-road / across-road" coords; the standard trick for lane/road following |
| Car-kinematic curves | `ReedsSheppPath`, `DubinsPath` | Non-holonomic (a car can't move sideways); needed for realistic paths |
| Smoothing | `QuinticPolynomialsPlanner`, `BezierPath`, `CubicSpline` | Turn a jagged grid path into a drivable curve |
| Path tracking (control) | `PathTracking/` → Pure Pursuit, Stanley, LQR, MPC | Your §7.4 controller — start with Pure Pursuit |
| Also present | `StateLatticePlanner`, `RRT`/`RRT*`, `PRM`, `ElasticBands`, `ModelPredictiveTrajectoryGenerator` | Alternatives if you want them |

**The whole global+local architecture in one line:** `hybrid_a_star_planning(...)` for the route → **DWA** or Frenet for real-time avoidance → **Pure Pursuit** to follow it. Published A*+DWA fusion work reports ~9.6% shorter paths and ~29% faster planning from exactly this pairing — a citable justification for the two-layer design.

> **Decision rule:** RoadRunner cosim if you have ADT access (sponsor points + least code). **PythonRobotics + CARLA/SUMO if not** (free, full control, best for a 2nd-year team, best mixed-traffic density). 2D BEV sim only as a last-resort demo that always runs. Log the choice in Appendix C.

---

# PART VII-C — RUNNABLE STARTER: the perception→planning bridge

**There is a working starter script shipped alongside this bible: `bridge_starter.py`.** It is the one thing the rest of the bible describes but you didn't have — the code that closes Gap 1 — and it runs *today*, standalone, on `numpy + scipy + matplotlib` (no MATLAB, no GPU, no dataset). Run it: `python3 bridge_starter.py` → writes `bridge_demo.png` (also included, so you can see the target output before running anything).

**What it does, end to end** — exactly the MVP loop from §3.2:

1. **Fake perception** — generates a BEV semantic map (5-class) + a per-cell confidence map, standing in for FusionSegNet's output. Same array shapes the real model produces after IPM.
2. **Occupancy** — road = free, everything else = obstacle.
3. **Cost map** — Euclidean-distance-transform obstacle inflation (per §7.1) **plus the uncertainty term (Idea B)**: low-confidence cells cost more, so the planner routes around and slows near them. This is your novelty, in ~4 lines.
4. **Global plan** — an 8-connected A* over the cost grid.
5. **Adaptive replan loop** — the ego drives the path; a pedestrian steps out from behind a parked car; once it's within the look-ahead distance, that region's cost is raised and the path is **replanned around it** — the continuous-cost analogue of the RoadRunner `replanPath` mechanism from VII-B.2.

**It is built to be grown, not thrown away.** Three tags mark where the real system slots in — search the file for `# >>> SWAP`:

- **`SWAP 1`** — replace `make_fake_perception()` with your FusionSegNet mask + confidence. Nothing downstream changes; the shapes already match.
- **`SWAP 2`** — replace the toy A* with PythonRobotics `hybrid_a_star_planning(start, goal, ox, oy, ...)` for car-like (non-holonomic) paths. The cost grid becomes the obstacle list `ox/oy`.
- **`SWAP 3`** — add behaviour-aware cost (Idea A) and occlusion cost (Idea C) into `build_cost_map()` via the `extra_cost` hook that's already wired in.

**Why this matters for your week:** it lets the planner/costmap teammate work *in parallel* with the perception teammate, against the fake upstream, from day one — the "fake upstream first" advice from Part XII, already done for you. The moment FusionSegNet produces real masks, you delete `make_fake_perception()` and the loop keeps running. And `bridge_demo.png` is, as-is, a legitimate slide for the demo: it visibly shows uncertainty-aware cost and hazard replanning.

> Treat it as scaffolding with your name to be written on it — it is intentionally simple (grid A*, a single scripted hazard) so you understand every line before a judge asks you to. Deepen it; don't just run it.

---

# PART VIII — TECH STACK

| Layer | Tool | Note |
|---|---|---|
| Perception | **PyTorch** (built) | export TorchScript/ONNX for the bridge |
| Auto-labelling | nuscenes-devkit, OpenCV, pyquaternion, shapely | the 4-voter fusion |
| Indian adaptation | IDD / IDD-3D / IDD-AW | target domain + weather benchmark |
| Costmap & planning | **MATLAB + ADT + Navigation Toolbox** | `vehicleCostmap`, `inflationCollisionChecker`, `validatorVehicleCostmap`, `plannerHybridAStar`, `plannerAStar`, `navGraph`, `optimizePath`, `controllerPurePursuit` (see Part VII-B) |
| Simulation | **RoadRunner Scenario cosim** (`roadrunnerSetup`, `createSimulation`) / **CARLA+SUMO** / 2D BEV fallback | replanning loop ships as an example; CARLA+SUMO for dense mixed traffic |
| Bridge | MATLAB Engine for Python, or ONNX import into MATLAB | run segmenter, plan in MATLAB |
| Control | Pure Pursuit → MPC | |
| Compute | Colab / Local Workstation (NVIDIA RTX 3050 6GB Laptop GPU, Windows 11) | |
| Deployment | TorchScript + ONNX; Jetson Nano/RPi story | frugal-retrofit angle |

> **The bridge is upside, not a dependency.** If it eats more than two days, do planning in Python (`numpy`, `shapely`, `scipy`) and keep MATLAB for a supporting scenario demo.

---

# PART IX — EVALUATION

**Perception**
- mIoU + **per-class IoU** (Road, Sidewalk, Vehicle, Human)
- **Binary drivable-space IoU** — the number planning actually depends on
- **nuScenes-val vs IDD-val** (the §2.2 table)
- **IDD-AW subset** — accuracy under rain/fog/night
- FPS, params, model size
- **Ablation:** confidence weighting / temporal loss / TTA / copy-paste / SE+attention

**Prediction** *(borrow these standard metrics from Argoverse / nuScenes so your numbers are comparable to the literature, not invented)*
- **ADE** (Average Displacement Error) — mean L2 distance between predicted and true positions over the horizon
- **FDE** (Final Displacement Error) — L2 error at the final predicted timestep
- **minADE_k / minFDE_k** — best of k predicted modes (report k=1 at minimum)
- **Miss rate** and **collision score** — the DeepUrban work shows augmenting training data cut collision score ~50%, a citable justification for your augmentation pipeline
- Standard protocol to state: *N s of history → M s of future* (nuScenes uses 2 s → 6 s; Argoverse 2 s → 3 s). Pick one and name it.

**Planning & avoidance**
- **Collision rate** over N scripted scenarios (target: 0 on the safe set)
- **Success rate** (goal reached, no violation)
- **Min TTC**, hard-brake count
- **Smoothness** (curvature, jerk)
- **Replanning latency** (real-time claim)
- **Adaptivity evidence:** speed vs perception-confidence plot; speed vs occlusion-density plot — *graphs that prove the word "adaptive"*

**Adopt the CARLA Driving Score as your composite metric** *(borrowed from the official CARLA Autonomous Driving Leaderboard — gives you one principled number instead of a pile of separate stats):*
> **Driving Score = Route Completion (%) × Infraction Penalty**, where the penalty is a product of multipliers each infraction subtracts (collisions with vehicles/pedestrians/static objects, running red lights, going off-road, route deviation, blocking traffic). A car that finishes the route but plows through a pedestrian scores near zero — exactly the right incentive. Report Route Completion and Driving Score separately so a judge sees both "did it finish" and "did it drive safely."

**Scenario checklist — script these (the CARLA leaderboard uses the NHTSA typology).** Cover as many as time allows and report per-scenario:
lane merging · lane changing · **negotiation at unsignalled intersections** (very Indian) · roundabout negotiation · handling traffic signs · **coping with pedestrians, cyclists, and other agents** (your jaywalker/wrong-way-auto/animal cases). Run each under **clear / rain / fog / night** to exercise your weather-augmentation claim.

**Headline KPI slide:** `Driving Score 71.8% · Route Completion 93.8% · 0 collisions across 16 NHTSA-type scenarios · 30.0 FPS perception · 49.97 ms replan · IDD mIoU 57.2% (unsupervised adaptation; IndiVNet 69.98% supervised for context)`

---

# PART X — RISK REGISTER

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | "This is perception, not planning" | **High** | **High** | Build the MVP loop; **lead the pitch with planning** |
| R2 | Wrong PS ID on submission | Med | **High** | Verify 26037 vs 26038 on the portal **today** |
| R3 | "nuScenes isn't India" | High | Med | The §2.2 reframe — gap as measured finding |
| R4 | "From scratch" claim exposed | Med | **High** | Fix Gap 3 now |
| R5 | Planner unfinished at deadline | Med | **High** | Ship Hybrid A* + reactive stop first; ideas A/C are additive |
| R6 | MATLAB bridge eats the week | Med | Med | Timebox to 2 days; Python fallback ready |
| R7 | Sim won't run on demo laptop | Med | High | Pre-record + keep the 2D BEV sim |
| R8 | IDD domain gap tanks accuracy | Med | Med | It's a *result*, not a failure — report it |
| R9 | Full stack too slow for real-time | Med | Med | TorchScript, downscale input, measure early |
| R10 | Colab timeout / lost weights | Low | Med | Checkpoint to Drive every epoch |

---

# PART XI — ROADMAP

**Phase 0 — Lock the story (Day 0–1)**
- [ ] Verify PS ID. Fix Gap 3. Choose ideas from Part VI. Name the system.

**Phase 1 — Perception solid**
- [ ] Finish nuScenes training; baseline + ablation numbers
- [ ] **Run the domain-gap experiment (§2.2)** — evaluate on IDD before adaptation
- [ ] Fine-tune/adapt to IDD; fill the recovery column
- [ ] Confidence-map demo visual

**Phase 2 — Close the loop (make-or-break)**
- [ ] **Start from `bridge_starter.py` (Part VII-C)** — the loop already runs against fake perception
- [ ] Segmentation → BEV costmap with EDT risk field *(SWAP 1: real FusionSegNet output)*
- [ ] Uncertainty term (Idea B) *(already in the starter)*
- [ ] Constant-velocity prediction + Hybrid A* *(SWAP 2: PythonRobotics)*
- [ ] Reactive avoidance + emergency stop
- [ ] Wire the full loop in sim

**Phase 3 — Adaptive + polish**
- [ ] Occlusion phantoms (Idea C)
- [ ] Behaviour-aware margins (Idea A) *if time*
- [ ] Port to MATLAB/RoadRunner *if time*
- [ ] Hazard scenario suite + all Part IX metrics

**Phase 4 — Pitch (final 1–2 days)**
- [ ] Record demo · build deck · rehearse Part XV · freeze code

---

# PART XII — LEARNING PATH (for a 2nd-year CSE student)

You have not been taught most of this yet. That's normal. Here's the honest dependency order — **learn each just deep enough to use it**, not exhaustively.

| Need | Prerequisite | Fastest path |
|---|---|---|
| Understand BEV/IPM | homogeneous coordinates, camera intrinsics/extrinsics, projective geometry | one good tutorial on the pinhole camera model + `cv2.warpPerspective` |
| Occupancy & cost maps | 2D grids, distance transforms | `scipy.ndimage.distance_transform_edt` — 20 minutes |
| Hybrid A* | A* search (you know this), plus non-holonomic constraints & Reeds-Shepp curves | read the Dolgov/Thrun paper's figures first, code second |
| Tracking | Kalman filter, Hungarian assignment | implement SORT — it's ~200 lines and teaches both |
| Prediction | linear extrapolation → sequence models | start with constant-velocity; don't jump to LSTMs |
| MPC | linear algebra, constrained optimisation | **skip unless you have spare weeks** — Pure Pursuit is enough |
| Behaviour classification (Idea A) | basic feature engineering + any classifier | thresholds first; CMetric's graph theory is a v2 |

**Meta-advice worth more than any of the above:** you are going to be tempted to add yet another clever idea instead of finishing the loop. **Don't.** A complete, working, modest pipeline beats a brilliant, half-wired one at every hackathon that has ever existed. Your notebook already has seven clever upgrades; what it doesn't have is a planner.

**Second meta-advice:** implement each module with a *fake* upstream first. Build the planner against a hand-drawn costmap before wiring real segmentation into it. You'll debug 5× faster and the modules stay independently testable.

---

# PART XIII — TEAM ROLES

| Workstream | Owner | Backup |
|---|---|---|
| Perception / FusionSegNet | Team Member 1 (Perception Lead) | Team Member 2 |
| Data / IDD adaptation & domain-gap experiment | Team Member 2 (Data Eng) | Team Member 1 |
| Costmap + planner | Team Member 3 (Planning Lead) | Team Member 4 |
| Prediction / tracking | Team Member 4 (Robotics Eng) | Team Member 3 |
| Simulation + MATLAB bridge | Team Member 5 (Simulation Eng) | Team Member 4 |
| Integration (owns the loop) | Team Member 3 (Planning Lead) | Team Member 5 |
| Pitch / deck / demo video | Team Member 6 (Presentation Lead) | Team Member 1 |
| Lead / bible keeper | Team Lead | Team Member 6 |

---

# PART XIV — PITCH & DEMO

## 14.1 The 30-second version

> *"Indian roads break every assumption self-driving cars are built on — no lanes, mixed traffic, animals, things appearing from behind buses. We built **MargDarshi-AV**. It learns to see drivable space with zero hand-labelled data by making four sensors vote on every pixel. It then plans a path that gets more cautious in three situations: when it isn't confident, when it can't see, and when the vehicle next to it is driving erratically. We measured how badly Western-trained models fail on Indian roads, and how much of that gap we close."*

## 14.2 Run of show (< 4 min)

| Time | Beat |
|---|---|
| 0:15 | **The problem** — one clip of real Indian traffic |
| 0:45 | **Perception** — FusionSegNet on an **IDD** clip; then the **confidence map** (your signature visual) |
| 0:30 | **Cost map forming** from segmentation + uncertainty |
| 1:30 | **The loop.** Hazard appears → replans/stops. Then: approaching a parked bus, it **slows before anything is visible** (occlusion). Then: same scene, erratic agent → wider berth. |
| 0:30 | **Numbers** — KPI slide + the domain-gap table |
| 0:15 | **Close** — frugal deployment + what's next |

## 14.3 What makes you memorable

1. The **confidence-map visual** — novel and instantly legible
2. **Zero-annotation labelling** — "we didn't pay for a single label"
3. **Caution you can see** — the car slowing for reasons the audience can follow
4. **A measured result**, not just a demo
5. **MathWorks-native** planning and simulation

---

# PART XV — JUDGE Q&A DRILL

**"This is segmentation — where's the planning?"**
Segmentation is our perception pillar. It feeds a BEV cost map that a Hybrid A* planner and a reactive avoidance layer use to produce and verify a trajectory. Here's the closed loop. *(demo)*

**"nuScenes is Singapore and Boston. Why is this relevant to India?"**
We train there because its HD maps and LiDAR let us auto-label with zero human annotation. Then we adapt to IDD and IDD-3D. And we measured the gap — published work shows detectors trained on Waymo and nuScenes fail on Indian unstructured traffic, so we quantified exactly how much we lose and how much we recover. That table is one of our results.

**"Did you use pretrained weights?"**
Yes — the EfficientNet-B0 encoder is ImageNet-pretrained and fine-tuned end-to-end. The decoder, ASPP, attention gates, and the entire fusion-labelling pipeline are ours, trained from scratch. *(Only say this after fixing Gap 3.)*

**"What's actually novel here?"**
Two things. Labels with no human annotation, via four sensors voting per pixel. And using that vote agreement twice — once to weight training, once as a caution signal in the planner. We haven't seen perception uncertainty propagated into the cost map this directly. And it's not a niche bet: the teams that win the CARLA challenge found that *label quality beats architecture* — so attacking labelling with zero annotation is aimed squarely at the field's real bottleneck.

**"What does 'adaptive' mean concretely?"**
Three inputs change our safety margin in real time: perception confidence, occluded area ahead, and per-agent behaviour aggression. Here are the speed-vs-confidence and speed-vs-occlusion plots.

**"What if perception is wrong?"**
Three layers. Low confidence raises cost, so we route around and slow down. Occluded regions get phantom agents, so we're cautious about what we can't see at all. And there's an always-available controlled stop if no safe trajectory exists.

**"Why Hybrid A* and not RL / end-to-end?"**
Interpretability and safety. We can inspect why a path was chosen and prove a fallback exists. End-to-end is a black box we couldn't certify in a hackathon timeframe — it's on our future-work slide.

**"Isn't this just the MathWorks RoadRunner example?"** *(they may know it — answer confidently)*
We build on it, and we say so. The stock example replans by setting a blocked lane's cost to infinity — a binary switch. Our extension makes that cost continuous and adaptive: each cell's cost rises with perception uncertainty, occlusion risk, and how aggressively nearby agents are driving. So the car doesn't just avoid fully-blocked lanes — it flows around graded risk, and slows before it can even see a hazard. Same integration point, fundamentally different behaviour on unstructured roads.

**"Does it run in real time?"**
Perception at 30.0 FPS via TorchScript (33.3 ms); replanning in 49.97 ms on local workstation (RTX 3050 GPU / multi-core CPU).

**"How would this deploy?"**
TorchScript/ONNX perception on an edge GPU; planning and control in Simulink, deployable via code generation. There's prior work running camera-LiDAR collision avoidance on a Raspberry Pi on Indian roads, so a low-cost retrofit path is realistic.

**"What doesn't work yet?"** *(answer this honestly — it builds more trust than any success claim)*
We acknowledge two real engineering limitations: we do not yet model multi-agent non-verbal game-theoretic negotiation at chaotic, unsignalled 4-way Indian intersections (Idea D), and our behaviour classifier is threshold-based rather than a learned spatio-temporal graph neural network (Idea E).

---

# PART XVI — INTEGRITY CHECKLIST

- [ ] PS ID verified against the official portal
- [ ] Writeup matches code on pretrained-vs-scratch
- [ ] Dataset licences respected — **IDD is CC BY-NC-SA 4.0**; nuScenes non-commercial terms; METEOR terms — and cited
- [ ] Every metric reproducible from the repo
- [ ] FPS/latency measured on stated hardware, not estimated
- [ ] Ablation numbers real, not placeholders
- [ ] All prior work credited (IDD/IDD-3D — Varma et al. & Dokania et al.; METEOR — Chandra et al.; Hybrid A* — Dolgov/Thrun; EfficientNet; ADT functions)
- [ ] Demo video matches what the code does
- [ ] No `[[placeholders]]` remaining

---

# APPENDIX A — GLOSSARY

**mIoU** mean Intersection-over-Union · **BEV** Bird's-Eye View · **IPM** Inverse Perspective Mapping (camera → top-down, assumes flat ground) · **ASPP** Atrous Spatial Pyramid Pooling · **SE block** Squeeze-and-Excitation channel attention · **Attention Gate** suppresses irrelevant skip features in U-Nets · **TTA** Test-Time Augmentation · **Pseudo-label** machine-generated training label · **TTC** Time-To-Collision · **EDT** Euclidean Distance Transform · **Hybrid A\*** non-holonomic grid planner · **APF** Artificial Potential Field · **MPC** Model Predictive Control · **DWA** Dynamic Window Approach · **RSS** Responsibility-Sensitive Safety · **Domain adaptation** making a model trained on one distribution work on another · **Non-holonomic** can't move sideways (a car; unlike a drone) · **IDD** Indian Driving Dataset (IIIT-H) · **ADT** Automated Driving Toolbox

---

# APPENDIX B — SOURCE ASSETS & LINKS

**Your assets:** `FusionSegNet_v5.ipynb` (cell map §4.6) · `best_fusionsegnet_v5.pth` (Drive) · `masks/`, `confidence/`, `paste_crops/`, `visualizations/` · **`bridge_starter.py`** + **`bridge_demo.png`** (the runnable Gap-1 bridge, Part VII-C)

**Datasets:** IDD https://idd.insaan.iiit.ac.in/ · IDD-3D https://idd3d.github.io/ · METEOR https://gamma.umd.edu/pro/autonomousdriving/meteor/ · nuScenes https://www.nuscenes.org/nuscenes · IDD-D YOLO-format on Kaggle (search "Indian Driving Dataset Detections YOLOv11")

**People/labs:** Rohan Chandra https://rohanchandra30.github.io/ · UMD GAMMA lab · IIIT-H CVIT (IDD authors)

**Papers:** METEOR arXiv:2109.07648 · IDD WACV 2019 (Varma et al.) · IDD-3D WACV 2023 (Dokania et al.) · Paden et al. motion planning survey

**Runnable examples (start here for the build):**
- Hybrid A* collision checking — mathworks.com/help/nav/ug/enable-vehicle-collision-checking-for-path-planning-using-hybrid-a-star.html
- Lane-Level Path Planning + replanning cosim — mathworks.com/help/driving/ug/lane-level-path-planning-with-roadrunner-scenario.html
- AEB with RoadRunner (Euro NCAP) — mathworks.com/help/driving/ug/autonomous-emergency-braking-with-roadrunner-scenario.html
- ADT product hub (incl. "Master Class: Decision Making, Path Planning, Control" video) — mathworks.com/products/automated-driving.html

**Simulators:** CARLA — github.com/carla-simulator/carla (CoRL'17, Dosovitskiy et al.) · CARLA↔SUMO co-sim — github.com/carla-simulator/carla/blob/master/Docs/adv_sumo.md · SUMO — sumo.dlr.de

**Planner code (no MATLAB):** PythonRobotics — github.com/AtsushiSakai/PythonRobotics (Hybrid A*, DWA, Frenet, Reeds-Shepp, Pure Pursuit; MIT)

**Full-stack references:** Autoware — github.com/autowarefoundation/autoware · openpilot — github.com/commaai/openpilot

**Competition winners:** TransFuser — github.com/autonomousvision/transfuser · carla_garage (TransFuser++) — github.com/autonomousvision/carla_garage · CARLA leaderboard harness — github.com/carla-simulator/leaderboard

**IDD segmentation baselines (comparables + splits):** IshanKuchroo/IDD-Indian-Driving-Dataset (16-class + 6991/1912/957 split) · AbhayVAshokan/Semantic-Segmentation-of-Road-Surface · DAYA7624/Semantic-Segmentation-on-Indian-Driving-Dataset · mohan-gupta/driving-scene-segmentation · karansspk462000/Road-Segmentation-For-Autonomous-Vehicles · IDD-3D devkit — github.com/shubham1810/idd3d_kit

**SOTA to benchmark against:** IndiVNet — 69.98% mIoU on IDD (Nature Sci. Reports 2025) · Inception U-Net + Grad-CAM on IDD-Lite (Sensors 2022) — adds explainability

**Prediction benchmarks/metrics:** Argoverse & Argoverse 2 · nuScenes prediction split · INTERACTION · nuPlan · Waymo Open Motion · DeepUrban (arXiv:2601.10554) — for ADE/FDE/collision-score

**Practical:** ADAS L0 on Indian Roads — https://github.com/AdroitAnandAI/ADAS-Collision-Avoidance-System-on-Indian-Roads

**SIH:** community PS repo https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements

---

# APPENDIX C — DECISION LOG

| Date | Decision / Question | Status |
|---|---|---|
| 2026-09-12 | **PS ID: 26037 or 26038?** | **RESOLVED → 26037.** Verified against the official SIH-2026 community dataset (NoBugNinja repo, scraped 2026-08-22): 26037 = "Adaptive Path Planning and Collision Avoidance for Autonomous Vehicles on Unstructured Indian Roads", Org MathWorks, Software, Robotics and Drones. 26038 = "Explainable AI for Diabetic Retinopathy Screening in Rural India" (a different PS). No discrepancy — the screenshot was correct. |
| 2026-09-12 | Pretrained vs scratch — which claim ships? | **Leaning Option A** (keep ImageNet-pretrained encoder; fix the writeup). PS 26037 text contains **no** pretrained-weights prohibition and even encourages Deep Learning Toolbox — so the "from scratch" rule was self-imposed, not an SIH rule (open Q1 answered). **Pending:** team ratification + the actual writeup edit in the FusionSegNet notebook (notebook lives on Drive, not in this repo). |
| 2026-09-12 | Which Part VI ideas are we building? | **RESOLVED → Build B + C + G, Stretch A, Slide-only D/E/F.** (Team decision.) |
| 2026-09-12 | Planner: Hybrid A* / lattice / APF / MPC | **RESOLVED → Hybrid A\* (global) + reactive local layer (DWA / short-horizon MPC).** (Team decision.) |
| 2026-09-12 | Sim: RoadRunner / CARLA / SUMO / 2D BEV | **RESOLVED → PythonRobotics + CARLA/SUMO** (2D BEV as last-resort demo fallback). ⚠️ Note the tension: PS 26037 explicitly asks for a MATLAB/Simulink + RoadRunner closed-loop pipeline. A MATLAB/RoadRunner port stays a Phase-3 additive (T3.5) for sponsor alignment. (Team decision.) |
| 2026-09-13 | MATLAB bridge — must-have or nice-to-have? | **RESOLVED → De-scoped** (no ADT license; pure PythonRobotics stack is primary demo per Bible VII-B.5). |
| 2026-09-13 | nuScenes ↔ IDD ↔ 5-class label remap table | **RESOLVED → Done.** Implemented in `perception/label_remap.py` (6/6 tests passing). |
| 2026-09-13 | System name | **RESOLVED → MargDarshi-AV** (मार्गदर्शी). |
| 2026-09-13 | Internal round & finale dates | Tracked per team schedule. |

**Open questions:**
1. ~~Do the SIH rules actually forbid pretrained weights, or was that self-imposed?~~ **Answered (2026-09-12): self-imposed.** PS 26037 has no such rule. Still confirm against the general SIH-2026 rulebook before finals, but no prohibition appears in the problem statement.
2. What compute exists beyond Colab for sim + planning?
3. Full simulator on the demo machine, or pre-record?
4. Can you get IDD-3D access in time? (It unlocks running the fusion pipeline on Indian data directly.)

---

*Bible v5. Keep it alive. When reality disagrees with this document, reality wins — update the document.*
