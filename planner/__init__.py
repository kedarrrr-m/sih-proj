"""
planner package — SIH 26037 Phase 2: Close the Loop (Make-or-Break)

Modules:
- perception_bridge: Ingestion of BEV semantic & confidence maps (T2.1 SWAP 1).
- costmap: Hardened EDT safety potential field with Idea B uncertainty cost (T2.2).
- hybrid_a_star: Kinematic non-holonomic Hybrid A* path planner (T2.3 SWAP 2).
- prediction: Constant-velocity & turn-rate dynamic agent extrapolation (T2.4).
- safety: Safety state machine & provable emergency-stop fallback (T2.4).
- sim_loop: Continuous closed-loop 2D simulation with dynamic replan (T2.5 & T2.6).
"""

from .perception_bridge import (
    BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN,
    GRID_H, GRID_W, CELL_M,
    generate_synthetic_perception,
    load_perception,
    seg_to_occupancy,
)
from .costmap import CostMap
from .hybrid_a_star import HybridAStarPlanner, PlanResult, normalize_angle
from .prediction import TrackedAgent, TrajectoryPredictor
from .safety import SafetyController, SafetyState
from .sim_loop import ClosedLoopSimulator
from .occlusion import compute_occlusion_mask, place_phantom_agents, compute_occlusion_cost
from .behaviour import BehaviourClass, classify_behaviour, compute_behaviour_cost
from .scenarios import Scenario, ScenarioRunner, get_base_scenarios, get_all_scenarios, apply_weather
from .driving_score import route_completion, infraction_penalty, driving_score, compute_suite_scores

__all__ = [
    "BACKGROUND", "ROAD", "SIDEWALK", "VEHICLE", "HUMAN",
    "GRID_H", "GRID_W", "CELL_M",
    "generate_synthetic_perception",
    "load_perception",
    "seg_to_occupancy",
    "CostMap",
    "HybridAStarPlanner",
    "PlanResult",
    "normalize_angle",
    "TrackedAgent",
    "TrajectoryPredictor",
    "SafetyController",
    "SafetyState",
    "ClosedLoopSimulator",
    "compute_occlusion_mask",
    "place_phantom_agents",
    "compute_occlusion_cost",
    "BehaviourClass",
    "classify_behaviour",
    "compute_behaviour_cost",
    "Scenario",
    "ScenarioRunner",
    "get_base_scenarios",
    "get_all_scenarios",
    "apply_weather",
    "route_completion",
    "infraction_penalty",
    "driving_score",
    "compute_suite_scores",
]

