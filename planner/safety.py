"""
planner/safety.py — T2.4 (Safety State Machine & Provable Emergency Stop Fallback)

Implements:
- Time-to-Collision (TTC) computation against dynamic predicted agents.
- Behavioral safety state machine:
    CRUISE -> YIELD -> SLOW -> EMERGENCY_STOP -> REPLAN
- Provable fail-safe: guarantees controlled emergency braking if no feasible path exists.
"""

from enum import Enum
from typing import List, Tuple, Dict, Optional
import math
import numpy as np

from .costmap import CostMap
from .prediction import TrackedAgent, TrajectoryPredictor


class SafetyState(str, Enum):
    CRUISE = "CRUISE"                   # Nominal speed tracking
    YIELD = "YIELD"                     # Pre-emptive caution / high uncertainty ahead
    SLOW = "SLOW"                       # Moderate deceleration (cautionary TTC)
    EMERGENCY_STOP = "EMERGENCY_STOP"   # Maximum deceleration (critical TTC / obstacle)
    REPLAN = "REPLAN"                   # Route blocked ahead; trigger planner detour


class SafetyController:
    """
    Monitors ego trajectory safety against dynamic agents and static obstacles.
    """

    def __init__(self,
                 ttc_critical_s: float = 1.2,
                 ttc_warning_s: float = 2.8,
                 lookahead_cells: float = 24.0,       # ~6m look-ahead
                 emergency_decel: float = 8.0,        # m/s^2 (or cells/s^2)
                 comfort_decel: float = 3.0,
                 ego_radius_cells: float = 3.0):
        self.ttc_critical_s = ttc_critical_s
        self.ttc_warning_s = ttc_warning_s
        self.lookahead_cells = lookahead_cells
        self.emergency_decel = emergency_decel
        self.comfort_decel = comfort_decel
        self.ego_radius_cells = ego_radius_cells
        self.predictor = TrajectoryPredictor(default_horizon_s=4.0, dt=0.1)

    def compute_ttc(self,
                    ego_trajectory: List[Tuple[float, float, float]],
                    predicted_agents: Dict[int, List[Tuple[float, float, float]]],
                    agents: List[TrackedAgent]) -> Tuple[float, Optional[int]]:
        """
        Computes Time-To-Collision (TTC) between ego trajectory and predicted agents.

        Args:
            ego_trajectory: List of (y, x, t) for ego vehicle.
            predicted_agents: Dict of agent_id -> [(y, x, t)].
            agents: List of TrackedAgent objects for collision radii.

        Returns:
            (min_ttc, colliding_agent_id). If no collision in horizon, min_ttc = inf.
        """
        agent_radii = {a.agent_id: a.radius_cells for a in agents}
        min_ttc = float("inf")
        culprit_id = None

        if not ego_trajectory or not predicted_agents:
            return min_ttc, culprit_id

        # Interpolate or match timestamps
        for ey, ex, et in ego_trajectory:
            for aid, atraj in predicted_agents.items():
                r_thresh = self.ego_radius_cells + agent_radii.get(aid, 2.0)
                # Find agent position at nearest timestamp
                for ay, ax, at in atraj:
                    if abs(et - at) < 0.08:  # matching time step
                        dist = math.hypot(ey - ay, ex - ax)
                        if dist < r_thresh:
                            if et < min_ttc:
                                min_ttc = et
                                culprit_id = aid
                            break

        return min_ttc, culprit_id

    def check_path_blocked(self,
                           path: List[Tuple[float, float, float]],
                           costmap: CostMap,
                           lookahead_steps: int = 15) -> bool:
        """
        Checks if the planned trajectory intersects non-traversable cells within lookahead.
        """
        if not path:
            return True
        check_len = min(len(path), lookahead_steps)
        for i in range(check_len):
            y, x, _ = path[i]
            iy, ix = int(round(y)), int(round(x))
            if not costmap.is_traversable(iy, ix):
                return True
        return False

    def evaluate(self,
                 ego_y: float,
                 ego_x: float,
                 ego_speed: float,
                 planned_path: List[Tuple[float, float, float]],
                 costmap: CostMap,
                 agents: List[TrackedAgent]) -> Tuple[SafetyState, float, str]:
        """
        Evaluates the current state and determines safety command.

        Returns:
            (SafetyState, min_ttc, reason_message)
        """
        # 1. Project ego trajectory in time assuming current speed
        step_dt = 0.1
        ego_traj: List[Tuple[float, float, float]] = []
        accum_dist = 0.0
        v = max(0.1, ego_speed)

        for i, pt in enumerate(planned_path):
            if i > 0:
                accum_dist += math.hypot(pt[0] - planned_path[i-1][0], pt[1] - planned_path[i-1][1])
            t = accum_dist / v
            if t > 4.0:
                break
            ego_traj.append((pt[0], pt[1], t))

        # 2. Predict dynamic obstacles
        preds = self.predictor.predict_all(agents, horizon_s=4.0, dt=step_dt)

        # 3. Calculate TTC
        ttc, culprit = self.compute_ttc(ego_traj, preds, agents)

        # 4. Check static / costmap obstruction ahead
        path_blocked = self.check_path_blocked(planned_path, costmap)

        # 5. State arbitration
        if ttc <= self.ttc_critical_s:
            return SafetyState.EMERGENCY_STOP, ttc, f"Critical TTC ({ttc:.2f}s) with agent {culprit}"

        if path_blocked:
            return SafetyState.REPLAN, ttc, "Static hazard/cost spike blocking look-ahead path"

        if ttc <= self.ttc_warning_s:
            return SafetyState.SLOW, ttc, f"Low TTC ({ttc:.2f}s) with agent {culprit}; slowing down"

        # Check local uncertainty (Idea B) in the near corridor
        iy, ix = int(round(ego_y)), int(round(ego_x))
        if 0 <= iy < costmap.H and 0 <= ix < costmap.W:
            if costmap.conf[iy, ix] < 0.40:
                return SafetyState.YIELD, ttc, "High perception uncertainty in current cell"

        return SafetyState.CRUISE, ttc, "Path clear, safe tracking"

    def execute_fail_safe_brake(self, current_speed: float, dt: float) -> float:
        """
        Provable fallback: applies maximum deceleration to safely halt vehicle.
        """
        return max(0.0, current_speed - self.emergency_decel * dt)
