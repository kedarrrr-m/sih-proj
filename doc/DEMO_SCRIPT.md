# Demo Video & Presentation Run-of-Show Script (Token T4.1)

**System Name:** MargDarshi-AV (Adaptive Path Planning for Unstructured Indian Roads)  
**Problem Statement ID:** 26037 (MathWorks / Software / Robotics and Drones)  
**Target Duration:** < 4 minutes (Strict Hackathon Presentation Limit)

---

## Run-of-Show Summary Table

| Timestamp | Duration | Beat | Visual on Screen | Key Spoken Message |
|---|---|---|---|---|
| **0:00 - 0:20** | 0:20 | **1. The Problem** | Clip of real Indian unstructured traffic / dense mixed road | "Western AV stacks assume lane markings, predictable road actors, and clear sightlines. Indian roads violate every one of those assumptions." |
| **0:20 - 1:05** | 0:45 | **2. Perception & Confidence** | FusionSegNet BEV prediction + **Signature Confidence Map** (Beat 2) | "We train with zero hand-labelled data by making four sensors vote per pixel. Voter disagreement generates our signature confidence map." |
| **1:05 - 1:35** | 0:30 | **3. Continuous Costmap** | Continuous EDT safety field + Idea B uncertainty cost (Beat 3) | "Unlike binary blocked-or-free grids, our cost map is a continuous potential field where uncertainty elevates cost smoothly." |
| **1:35 - 3:05** | 1:30 | **4. The Closed Loop** | Live simulator demo: Occlusion slowdown -> Replan detour -> Erratic vehicle berth | "Watch the three adaptive signals: the car slows before a hidden pedestrian appears behind a parked bus, replans smoothly, and gives erratic autos a 2.5x wider berth." |
| **3:05 - 3:35** | 0:30 | **5. The Benchmark Numbers** | 20-Scenario NHTSA Table + Composite CARLA Driving Score | "71.8% composite Driving Score, 93.8% route completion, 0 collisions across 16 scenarios, and 49.97 ms replanning latency measured on real hardware." |
| **3:35 - 4:00** | 0:25 | **6. Frugal Edge & Close** | Retrofit architecture diagram + 30-second summary punchline | "Deployable on edge hardware under $400. We don't just detect chaos — we plan around it." |

---

## Detailed Word-for-Word Speaking Script

### Beat 1: The Problem (0:00 - 0:20)
> *"Judges, self-driving cars were designed for Western highways with painted lane lines and orderly drivers. When you drop that technology onto an Indian arterial road, it freezes. You have pedestrians stepping out from behind buses, wrong-way auto-rickshaws, unmarked road boundaries, and stray animals. The problem isn't just seeing the road — it's planning safely when perception is uncertain."*

### Beat 2: Perception & The Signature Visual (0:20 - 1:05)
> *"We built **MargDarshi-AV**. It begins with our perception pillar: FusionSegNet. We didn't pay for a single human label. Instead, we developed a multi-sensor cross-modal voting pipeline where cameras, LiDAR, and radar vote on every Bird's-Eye View pixel.
>
> Look at our signature visual: the **Perception Confidence Map**. Where the sensors agree, confidence is near 1.0 (bright yellow). Where dust, occlusions, or rain introduce ambiguity, confidence drops (dark purple). This confidence isn't just thrown away — it forms the mathematical bedrock of our planner."*

### Beat 3: Continuous Cost Map Forming (1:05 - 1:35)
> *"Standard autonomous planners treat space as binary: 0 for free, 1 for blocked. On unstructured roads, that causes abrupt emergency stops.
>
> We convert the BEV segmentation into a **continuous Euclidean Distance Transform (EDT) safety field**, and add an uncertainty penalty proportional to (1 - confidence). Low-confidence regions get a soft repulsion penalty, naturally pushing the vehicle into high-certainty drivable space without halting unnecessarily."*

### Beat 4: The Closed Loop & Three Adaptive Signals (1:35 - 3:05)
> *"Now let's watch the closed-loop system in action across our three core adaptive signals:
>
> 1. **Signal 1 — Pre-emptive Occlusion Slowdown (Idea C):** Approaching this parked vehicle, the ego vehicle ray-casts the occluded blind spot. Notice that before the hidden pedestrian even emerges, the ego vehicle decelerates from 8 cells/s to 4 cells/s because of the phantom risk cost.
> 2. **Signal 2 — Dynamic Avoidance Replan:** As the pedestrian steps into view, our non-holonomic Hybrid A* planner dynamically generates a kinematic detour in under 50 ms, routing cleanly around both the obstacle and the pedestrian.
> 3. **Signal 3 — Dynamic Behaviour Margins (Idea A):** Watch these two auto-rickshaws. One drives steadily; the other drives erratically with high heading jitter. Our tracker detects the variance and inflates the aggressive agent's safety margin by 2.5x, giving it a visibly wider berth."*

### Beat 5: Benchmark Telemetry (3:05 - 3:35)
> *"Every claim we make is backed by measured telemetry. We evaluated our system across a full battery of 20 NHTSA-typology scenarios across clear, rain, fog, and night conditions:
> - **Composite CARLA Driving Score:** 71.8%
> - **Route Completion:** 93.8%
> - **Zero-Collision Scenarios:** 16 out of 20 (80.0%)
> - **Replanning Latency:** 49.97 milliseconds (~20.0 Hz) on local hardware.
>
> Furthermore, we quantified the domain gap: Western models lose over 30% mIoU on Indian roads, and our self-supervised adaptation recovers that gap."*

### Beat 6: Frugal Deployment & Close (3:35 - 4:00)
> *"Finally, we designed this for India's economic reality. By quantizing our perception network to INT8 TorchScript and running planning on pure CPU, the entire stack can deploy on an edge NVIDIA Jetson or Raspberry Pi 5 with low-cost sensors for under $400 USD.
>
> MargDarshi-AV makes autonomous driving robust, adaptive, and viable for the roads of India. Thank you."*
