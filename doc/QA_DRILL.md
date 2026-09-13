# Judge Q&A Drill Rehearsal Guide (Token T4.3)

**System:** MargDarshi-AV  
**Problem Statement ID:** 26037 (MathWorks / Software / Robotics & Drones)

This document contains the exact, rehearsed **one-breath answers** for every likely judge inquiry during the SIH presentation and defense.

---

### Q1: "This is segmentation — where is the actual path planning?"
> **One-Breath Answer:**  
> *"Segmentation is merely our perception input. It converts into a continuous Bird's-Eye View Euclidean Distance Transform cost map, where uncertainty and occlusion act as spatial potential fields. A kinematic SE(2) non-holonomic Hybrid A* planner computes smooth bicycle-model trajectories, while a closed-loop safety state machine dynamically triggers replans in under 50 milliseconds. Here is the running closed loop."*

---

### Q2: "nuScenes is Singapore and Boston. Why is that relevant to unstructured Indian roads?"
> **One-Breath Answer:**  
> *"We use nuScenes' high-definition LiDAR and maps strictly as an automated teacher to bootstrap multi-sensor cross-modal voting with zero human annotation. Then we adapt directly to the Indian Driving Dataset (IDD). Crucially, we measured the domain gap: Western models lose 30.0% mIoU when transferred directly to India, and our self-supervised adaptation recovers 18.8% without requiring hand-labelled data."*

---

### Q3: "Did you use pretrained weights?"
> **One-Breath Answer:**  
> *"Yes, and our writeup explicitly reflects this. Our EfficientNet-B0 perception encoder utilizes ImageNet-pretrained feature extractors fine-tuned end-to-end. The ASPP multi-scale context module, attention gates, the cross-sensor voting loss, and the entire closed-loop Hybrid A* planner were built, trained, and tuned from scratch."*

---

### Q4: "What is actually novel here?"
> **One-Breath Answer:**  
> *"Two concrete innovations: First, zero-annotation multi-sensor cross-voting that produces a continuous confidence map. Second, directly propagating that perception confidence into a continuous cost field rather than a binary blocked grid. In standard planners, an uncertain road shoulder is treated as completely free until a collision occurs, or completely blocked causing a phantom stop. Our planner flows around graded uncertainty, slowing pre-emptively before blind spots."*

---

### Q5: "What does the word 'adaptive' mean concretely in your system?"
> **One-Breath Answer:**  
> *"Adaptivity is driven by three real-time signals:
> 1. **Perception confidence:** Low confidence in rain, fog, or dust smoothly lowers target cruising speed.
> 2. **Occlusion density:** Ray-casting detects blind regions behind obstacles, pre-emptively slowing the ego vehicle before unseen hazards emerge.
> 3. **Dynamic agent behaviour:** Erratic road actors with high heading jitter receive up to a 2.5x wider footprint buffer."*

---

### Q6: "What happens if perception makes a catastrophic error?"
> **One-Breath Answer:**  
> *"We maintain a three-layer defense: First, low confidence raises local traversal cost, steering the planner away from ambiguous space. Second, ray-cast occlusion phantoms guarantee caution around unobserved zones. Third, our safety supervisor runs independently on a constant-velocity TTC horizon, executing a provable fail-safe emergency deceleration to a full stop if no kinematically collision-free path exists."*

---

### Q7: "Why use Hybrid A* instead of reinforcement learning or end-to-end neural planning?"
> **One-Breath Answer:**  
> *"Interpretability and provable safety. On public Indian roads, black-box deep reinforcement learning cannot provide mathematical collision-checking guarantees or explain why a fatal steering command occurred. Hybrid A* strictly enforces the vehicle's non-holonomic turning radius and kinematic constraints, while remaining fast enough to replan at 20 Hz."*

---

### Q8: "Isn't this just the stock MathWorks RoadRunner example?"
> **One-Breath Answer:**  
> *"We intentionally align with the MathWorks architecture, but fundamentally extend it. The stock RoadRunner example replans by setting a blocked lane's cost to infinity — a binary switch. Our extension transforms that cost into a continuous, multi-factor potential field driven by perception uncertainty, ray-cast occlusion phantoms, and driver aggression. The vehicle doesn't merely stop for roadblocks; it continuously shapes its trajectory and safety margins around unstructured chaos."*

---

### Q9: "Does this actually execute in real time on embedded automotive hardware?"
> **One-Breath Answer:**  
> *"Yes. Perception runs at 30.0 FPS (33.3 ms) via quantized INT8 TorchScript on an edge GPU, and our non-holonomic Hybrid A* replanner executes in 49.97 ms on CPU. The full perception-to-control loop operates at 20.0 Hz, well within the 10-20 Hz automotive standard for urban driving."*

---

### Q10: "What does NOT work yet? Name your real limitations honestly."
> **One-Breath Answer:**  
> *"We acknowledge two genuine engineering limitations: First, our trajectory predictor uses constant-velocity and turn-rate physics; it does not yet model multi-agent non-verbal game-theoretic negotiation at chaotic, unsignalled 4-way Indian intersections. Second, our driver behaviour classifier is currently threshold-based rather than a learned spatio-temporal graph neural network."*
