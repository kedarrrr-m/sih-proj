"""
planner/costmap.py — T2.2 (Hardened BEV Cost Map: EDT + Idea B Uncertainty Cost)

Implements the continuous-cost BEV safety field.
Features:
- Euclidean Distance Transform (EDT) safety potential field for smooth obstacle repulsion.
- Hard vehicle-radius inflation: dist <= vehicle_radius_cells is strictly blocked (np.inf).
- Idea B: continuous uncertainty penalty = uncertainty_weight * (1.0 - conf).
- extra_cost hook for Idea A (behaviour margins) and Idea C (occlusion phantom agents).
"""

from typing import Optional, Tuple, List
import numpy as np
from scipy.ndimage import distance_transform_edt


class CostMap:
    """
    2D BEV Cost Map representing navigability, safety margin, and uncertainty risk.
    """

    def __init__(self,
                 occ: np.ndarray,
                 conf: Optional[np.ndarray] = None,
                 cell_m: float = 0.25,
                 vehicle_radius_cells: int = 3,
                 uncertainty_weight: float = 6.0,
                 k_prox: float = 10.0,
                 extra_cost: Optional[np.ndarray] = None):
        """
        Builds the hardened cost map.

        Args:
            occ: (H, W) uint8 binary occupancy grid (0 = free drivable, 1 = obstacle).
            conf: Optional (H, W) float32 confidence map in [0.0, 1.0].
            cell_m: Metres per grid cell resolution.
            vehicle_radius_cells: Radius (in cells) of vehicle footprint hard inflation.
            uncertainty_weight: Multiplier for perception uncertainty (Idea B).
            k_prox: Gain for proximity-to-obstacle cost decay (1 / dist).
            extra_cost: Optional (H, W) additive cost grid (e.g. Ideas A & C).
        """
        self.H, self.W = occ.shape
        self.cell_m = float(cell_m)
        self.vehicle_radius_cells = int(vehicle_radius_cells)
        self.uncertainty_weight = float(uncertainty_weight)
        self.k_prox = float(k_prox)

        self.occ = occ.astype(np.uint8)
        self.conf = conf.astype(np.float32) if conf is not None else np.ones_like(occ, dtype=np.float32)

        # 1. Compute EDT: distance from every free cell to nearest obstacle
        free = (self.occ == 0)
        self.dist = distance_transform_edt(free).astype(np.float32)

        # 2. Smooth proximity cost: repels planner away from edges without sharp cliffs
        with np.errstate(divide="ignore"):
            proximity_cost = np.where(self.dist > 0, self.k_prox / self.dist, 0.0)
        base = 1.0 + proximity_cost

        # 3. Idea B: Uncertainty penalty (lower confidence -> higher cost)
        uncertainty_cost = self.uncertainty_weight * (1.0 - np.clip(self.conf, 0.0, 1.0))

        # 4. Total continuous cost
        self.grid = (base + uncertainty_cost).astype(np.float32)

        # 5. Apply SWAP 3 extra_cost hook (Idea A behavior / Idea C occlusion)
        if extra_cost is not None:
            self.grid += extra_cost.astype(np.float32)

        # 6. Hard-block obstacle cells and vehicle clearance zone
        self.grid[self.dist <= self.vehicle_radius_cells] = np.inf
        self.grid[self.occ == 1] = np.inf

    def is_traversable(self, y: int, x: int) -> bool:
        """Returns True if cell (y, x) is within bounds and finite cost."""
        if 0 <= y < self.H and 0 <= x < self.W:
            return np.isfinite(self.grid[y, x])
        return False

    def get_cost(self, y: int, x: int) -> float:
        """Returns cell cost or inf if out of bounds."""
        if 0 <= y < self.H and 0 <= x < self.W:
            return float(self.grid[y, x])
        return float(np.inf)

    def get_obstacle_coords(self, metric: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns coordinate arrays (ys, xs) where cells are non-traversable (inf).
        """
        blocked = ~np.isfinite(self.grid)
        ys, xs = np.nonzero(blocked)
        if metric:
            return ys.astype(np.float32) * self.cell_m, xs.astype(np.float32) * self.cell_m
        return ys, xs

    def inflate_obstacle(self, center_y: int, center_x: int,
                         radius_cells: int, cost_val: float = np.inf) -> None:
        """
        Inflates a dynamic circular obstacle in-place.
        """
        yy, xx = np.ogrid[:self.H, :self.W]
        mask = ((yy - center_y) ** 2 + (xx - center_x) ** 2) <= (radius_cells ** 2)
        self.grid[mask] = cost_val

    def copy(self) -> "CostMap":
        """Returns an independent deep copy."""
        new_map = CostMap.__new__(CostMap)
        new_map.H = self.H
        new_map.W = self.W
        new_map.cell_m = self.cell_m
        new_map.vehicle_radius_cells = self.vehicle_radius_cells
        new_map.uncertainty_weight = self.uncertainty_weight
        new_map.k_prox = self.k_prox
        new_map.occ = self.occ.copy()
        new_map.conf = self.conf.copy()
        new_map.dist = self.dist.copy()
        new_map.grid = self.grid.copy()
        return new_map
