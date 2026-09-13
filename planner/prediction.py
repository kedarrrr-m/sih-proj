"""
planner/prediction.py — T2.4 (Dynamic Agent Trajectory Prediction)

Implements constant-velocity and constant-turn-rate motion extrapolation for tracked agents.
Provides predicted spatio-temporal trajectories over a given lookahead horizon.
"""

from typing import List, Tuple, Dict
from dataclasses import dataclass, field
import math


@dataclass
class TrackedAgent:
    """Represents a dynamic tracked road agent in BEV grid coordinates."""
    agent_id: int
    agent_type: str                  # "vehicle", "pedestrian", "cyclist", "auto"
    y: float                         # grid row position
    x: float                         # grid col position
    vy: float                        # velocity in cells/s along y
    vx: float                        # velocity in cells/s along x
    yaw: float = 0.0                 # heading angle in radians
    yaw_rate: float = 0.0            # turn rate in rad/s
    radius_cells: float = 2.0        # conservative clearance radius
    history: List[Tuple[float, float]] = field(default_factory=list)

    @property
    def speed(self) -> float:
        return math.hypot(self.vy, self.vx)


class TrajectoryPredictor:
    """
    Extrapolates future positions of tracked road agents over a time horizon.
    """

    def __init__(self, default_horizon_s: float = 3.0, dt: float = 0.1):
        self.default_horizon_s = default_horizon_s
        self.dt = dt

    def predict_single(self,
                       agent: TrackedAgent,
                       horizon_s: float = None,
                       dt: float = None) -> List[Tuple[float, float, float]]:
        """
        Extrapolates a single agent's trajectory.

        Returns:
            List of (y_pred, x_pred, timestamp_sec)
        """
        h = horizon_s if horizon_s is not None else self.default_horizon_s
        step = dt if dt is not None else self.dt
        steps = int(math.ceil(h / step))

        traj: List[Tuple[float, float, float]] = []
        curr_y = agent.y
        curr_x = agent.x
        curr_yaw = agent.yaw
        speed = agent.speed

        for i in range(steps + 1):
            t = round(i * step, 4)
            traj.append((curr_y, curr_x, t))

            # Motion update: constant-turn-rate if yaw_rate != 0, else constant-velocity
            if abs(agent.yaw_rate) > 1e-3:
                curr_yaw += agent.yaw_rate * step
                curr_x += speed * math.cos(curr_yaw) * step
                curr_y += speed * math.sin(curr_yaw) * step
            else:
                curr_y += agent.vy * step
                curr_x += agent.vx * step

        return traj

    def predict_all(self,
                    agents: List[TrackedAgent],
                    horizon_s: float = None,
                    dt: float = None) -> Dict[int, List[Tuple[float, float, float]]]:
        """
        Extrapolates trajectories for all tracked agents.
        """
        return {agent.agent_id: self.predict_single(agent, horizon_s, dt) for agent in agents}
