"""
planner/hybrid_a_star.py — T2.3 (SWAP 2: Non-Holonomic Kinematic Hybrid A* Planner)

Implements SE(2) Hybrid A* path planning over the continuous BEV cost map.
Replaces toy 8-connected A* with a non-holonomic, car-like kinematic planner.

Features:
- Discrete bicycle kinematic model with forward/reverse motion primitives.
- Bounded curvature (minimum turning radius R_min = Wheelbase / tan(delta_max)).
- Continuous cost integration from CostMap (EDT proximity + Idea B uncertainty).
- Steering angle penalty and steering change (smoothness) penalty.
- Multi-circle vehicle footprint collision checking against inflated costmap.
- 2D Dijkstra heuristic computed over the costmap to guide SE(2) search around obstacles.
- Degenerate / narrow corridor infeasibility detection with clear reporting.
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import heapq
import math
import numpy as np

from .costmap import CostMap


def normalize_angle(theta: float) -> float:
    """Normalizes angle to [-pi, pi)."""
    return (theta + math.pi) % (2.0 * math.pi) - math.pi


@dataclass
class PlanResult:
    """Encapsulates planner output and telemetry."""
    success: bool
    path: List[Tuple[float, float, float]]  # List of (y_grid, x_grid, yaw_rad)
    cost: float
    nodes_expanded: int
    message: str = "OK"

    @property
    def grid_path(self) -> List[Tuple[int, int]]:
        """Returns integer (y, x) cell path for plotting and downstream drive loop."""
        return [(int(round(p[0])), int(round(p[1]))) for p in self.path]

    @property
    def curvatures(self) -> List[float]:
        """Estimates path curvature kappa along the trajectory."""
        if len(self.path) < 3:
            return [0.0] * len(self.path)
        curvs = [0.0]
        for i in range(1, len(self.path) - 1):
            dy1 = self.path[i][0] - self.path[i - 1][0]
            dx1 = self.path[i][1] - self.path[i - 1][1]
            dy2 = self.path[i + 1][0] - self.path[i][0]
            dx2 = self.path[i + 1][1] - self.path[i][1]
            ds1 = math.hypot(dy1, dx1)
            ds2 = math.hypot(dy2, dx2)
            if ds1 < 1e-4 or ds2 < 1e-4:
                curvs.append(0.0)
                continue
            d_yaw = normalize_angle(self.path[i + 1][2] - self.path[i][2])
            curvs.append(abs(d_yaw) / ((ds1 + ds2) * 0.5))
        curvs.append(0.0)
        return curvs


class NodeSE2:
    __slots__ = ("y", "x", "yaw", "cost", "h_cost", "parent", "steer", "direction")

    def __init__(self, y: float, x: float, yaw: float,
                 cost: float, h_cost: float,
                 parent: Optional["NodeSE2"] = None,
                 steer: float = 0.0,
                 direction: int = 1):
        self.y = y
        self.x = x
        self.yaw = yaw
        self.cost = cost
        self.h_cost = h_cost
        self.parent = parent
        self.steer = steer
        self.direction = direction

    @property
    def f_cost(self) -> float:
        return self.cost + self.h_cost

    def __lt__(self, other: "NodeSE2") -> bool:
        return self.f_cost < other.f_cost


class HybridAStarPlanner:
    """
    Kinematic Non-Holonomic Hybrid A* Planner operating directly on the BEV CostMap.
    """

    def __init__(self,
                 wheelbase_m: float = 2.5,
                 max_steer_rad: float = 0.60,       # ~34 degrees
                 step_size_cells: float = 1.8,     # motion primitive step length
                 xy_resolution_cells: float = 1.0, # 3D grid cell spatial bin
                 yaw_bins: int = 24,               # 15 degrees per heading bin
                 c_steer: float = 1.5,             # penalty for steering angle
                 c_dsteer: float = 3.0,            # penalty for steering change
                 c_reverse: float = 4.0):          # penalty for reverse gear
        self.wheelbase_m = wheelbase_m
        self.max_steer_rad = max_steer_rad
        self.min_turning_radius_m = wheelbase_m / math.tan(max_steer_rad)
        self.step_size = step_size_cells
        self.xy_res = xy_resolution_cells
        self.yaw_bins = yaw_bins
        self.yaw_res = (2.0 * math.pi) / yaw_bins

        self.c_steer = c_steer
        self.c_dsteer = c_dsteer
        self.c_reverse = c_reverse

        # Discrete steering choices: hard left, soft left, straight, soft right, hard right
        self.steer_inputs = [
            -self.max_steer_rad,
            -self.max_steer_rad * 0.5,
            0.0,
            self.max_steer_rad * 0.5,
            self.max_steer_rad,
        ]

    def _compute_2d_heuristic(self, costmap: CostMap, goal_y: int, goal_x: int) -> np.ndarray:
        """
        Computes 2D Dijkstra distance transform from goal across costmap.
        Provides admissible guidance around static obstacles.
        """
        H, W = costmap.H, costmap.W
        h_grid = np.full((H, W), np.inf, dtype=np.float32)

        if not costmap.is_traversable(goal_y, goal_x):
            return h_grid

        q = [(0.0, goal_y, goal_x)]
        h_grid[goal_y, goal_x] = 0.0

        nbrs = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]

        while q:
            d, y, x = heapq.heappop(q)
            if d > h_grid[y, x]:
                continue
            for dy, dx, dist_step in nbrs:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and np.isfinite(costmap.grid[ny, nx]):
                    step_cost = dist_step * max(1.0, float(costmap.grid[ny, nx]) * 0.2)
                    new_dist = d + step_cost
                    if new_dist < h_grid[ny, nx]:
                        h_grid[ny, nx] = new_dist
                        heapq.heappush(q, (new_dist, ny, nx))

        return h_grid

    def _check_collision(self, costmap: CostMap, y: float, x: float, yaw: float) -> bool:
        """
        Multi-circle footprint collision check against the CostMap.
        Returns True if in collision / non-traversable.
        """
        # Vehicle length ~ 4.0m (~16 cells), wheelbase ~ 2.5m (~10 cells)
        # Check rear axle, center, and front bumper
        cell_m = costmap.cell_m
        offsets_m = [-1.0, 0.5, 2.0]  # relative to center in meters
        for off_m in offsets_m:
            off_cells = off_m / cell_m
            # Moving along heading:
            # yaw = -pi/2 points along -y (towards top of grid / row 0)
            # yaw = 0 points along +x
            cy = int(round(y + off_cells * math.sin(yaw)))
            cx = int(round(x + off_cells * math.cos(yaw)))
            if not costmap.is_traversable(cy, cx):
                return True
        return False

    def _state_to_index(self, y: float, x: float, yaw: float) -> Tuple[int, int, int]:
        iy = int(math.floor(y / self.xy_res))
        ix = int(math.floor(x / self.xy_res))
        norm_yaw = (yaw + 2.0 * math.pi) % (2.0 * math.pi)
        iyaw = int(math.floor(norm_yaw / self.yaw_res)) % self.yaw_bins
        return iy, ix, iyaw

    def plan(self,
             costmap: CostMap,
             start_pose: Tuple[float, float, float],
             goal_pose: Tuple[float, float, float],
             max_iterations: int = 15000,
             allow_reverse: bool = False) -> PlanResult:
        """
        Plans non-holonomic path from start_pose to goal_pose on the CostMap.

        Args:
            costmap: Configured CostMap.
            start_pose: (y, x, yaw_rad) in grid cells and radians.
            goal_pose: (y, x, yaw_rad) in grid cells and radians.
            max_iterations: Search iteration budget.
            allow_reverse: Enable reverse gear expansions.

        Returns:
            PlanResult with trajectory and status.
        """
        sy, sx, syaw = start_pose
        gy, gx, gyaw = goal_pose

        # Validation of start and goal
        if not costmap.is_traversable(int(round(sy)), int(round(sx))):
            return PlanResult(
                success=False, path=[], cost=np.inf, nodes_expanded=0,
                message="Start position is in obstacle or non-drivable space."
            )
        if not costmap.is_traversable(int(round(gy)), int(round(gx))):
            return PlanResult(
                success=False, path=[], cost=np.inf, nodes_expanded=0,
                message="Goal position is in obstacle or non-drivable space."
            )

        # Compute 2D heuristic field
        h_grid = self._compute_2d_heuristic(costmap, int(round(gy)), int(round(gx)))
        if not np.isfinite(h_grid[int(round(sy)), int(round(sx))]):
            return PlanResult(
                success=False, path=[], cost=np.inf, nodes_expanded=0,
                message="No 2D path exists: corridor is completely blocked or too narrow."
            )

        start_h = float(h_grid[int(round(sy)), int(round(sx))])
        start_node = NodeSE2(sy, sx, syaw, cost=0.0, h_cost=start_h)

        open_set: List[Tuple[float, int, NodeSE2]] = []
        node_counter = 0
        heapq.heappush(open_set, (start_node.f_cost, node_counter, start_node))

        closed_set: Dict[Tuple[int, int, int], float] = {}
        directions = [1] if not allow_reverse else [1, -1]
        wheelbase_cells = self.wheelbase_m / costmap.cell_m

        goal_dist_thresh = 3.0  # cells (~0.75m)
        best_node = None
        min_goal_dist = float("inf")

        for iteration in range(max_iterations):
            if not open_set:
                break

            _, _, current = heapq.heappop(open_set)

            # Check goal condition
            dist_to_goal = math.hypot(current.y - gy, current.x - gx)
            if dist_to_goal < min_goal_dist:
                min_goal_dist = dist_to_goal
                best_node = current

            yaw_diff = abs(normalize_angle(current.yaw - gyaw))
            if dist_to_goal <= goal_dist_thresh and yaw_diff < math.radians(45.0):
                # Goal reached
                path = self._reconstruct_path(current)
                # Snap exact goal pose at end
                path.append((gy, gx, gyaw))
                return PlanResult(
                    success=True,
                    path=path,
                    cost=current.cost,
                    nodes_expanded=iteration + 1,
                    message="Goal reached successfully."
                )

            c_idx = self._state_to_index(current.y, current.x, current.yaw)
            if c_idx in closed_set and closed_set[c_idx] <= current.cost:
                continue
            closed_set[c_idx] = current.cost

            # Expand kinematic motion primitives
            for direction in directions:
                for steer in self.steer_inputs:
                    # Bicycle model integration along arc
                    ds = self.step_size * direction
                    d_yaw = (ds / wheelbase_cells) * math.tan(steer)
                    next_yaw = normalize_angle(current.yaw + d_yaw)

                    # Midpoint approximation for curve
                    mid_yaw = normalize_angle(current.yaw + d_yaw * 0.5)
                    # Coordinates in BEV: yaw=0 -> +x, yaw=-pi/2 -> -y
                    next_x = current.x + ds * math.cos(mid_yaw)
                    next_y = current.y + ds * math.sin(mid_yaw)

                    # Bounds check
                    iy, ix = int(round(next_y)), int(round(next_x))
                    if not (0 <= iy < costmap.H and 0 <= ix < costmap.W):
                        continue

                    # Collision check with car footprint
                    if self._check_collision(costmap, next_y, next_x, next_yaw):
                        continue

                    # Traversal and motion penalty costs
                    cell_cost = costmap.get_cost(iy, ix)
                    if not np.isfinite(cell_cost):
                        continue

                    edge_cost = abs(ds) * (1.0 + cell_cost * 0.1)
                    edge_cost += self.c_steer * abs(steer) * abs(ds)
                    edge_cost += self.c_dsteer * abs(steer - current.steer)
                    if direction < 0:
                        edge_cost += self.c_reverse * abs(ds)

                    next_cost = current.cost + edge_cost

                    # Heuristic lookup
                    h_val = float(h_grid[iy, ix])
                    if not np.isfinite(h_val):
                        continue

                    n_idx = self._state_to_index(next_y, next_x, next_yaw)
                    if n_idx in closed_set and closed_set[n_idx] <= next_cost:
                        continue

                    next_node = NodeSE2(
                        y=next_y, x=next_x, yaw=next_yaw,
                        cost=next_cost, h_cost=h_val,
                        parent=current, steer=steer, direction=direction
                    )
                    node_counter += 1
                    heapq.heappush(open_set, (next_node.f_cost, node_counter, next_node))

        # If strict goal wasn't met, check if best_node was close enough
        if best_node is not None and min_goal_dist <= goal_dist_thresh * 1.5:
            path = self._reconstruct_path(best_node)
            path.append((gy, gx, gyaw))
            return PlanResult(
                success=True,
                path=path,
                cost=best_node.cost,
                nodes_expanded=iteration + 1,
                message="Sub-goal reached near target."
            )

        return PlanResult(
            success=False,
            path=[],
            cost=np.inf,
            nodes_expanded=iteration + 1,
            message=f"Planner exhausted {max_iterations} iterations without finding a safe non-holonomic path (min dist: {min_goal_dist:.2f})."
        )

    def _reconstruct_path(self, node: NodeSE2) -> List[Tuple[float, float, float]]:
        path = []
        curr = node
        while curr is not None:
            path.append((curr.y, curr.x, curr.yaw))
            curr = curr.parent
        return path[::-1]
