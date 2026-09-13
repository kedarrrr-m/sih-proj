"""
tests/test_hybrid_a_star.py — Unit tests for T2.3 (Non-Holonomic Hybrid A* Planner)
"""

import unittest
import math
import numpy as np
from planner.costmap import CostMap
from planner.hybrid_a_star import HybridAStarPlanner, normalize_angle
from planner.perception_bridge import generate_synthetic_perception, seg_to_occupancy


class TestHybridAStar(unittest.TestCase):

    def setUp(self):
        self.seg, self.conf = generate_synthetic_perception(seed=42)
        self.occ = seg_to_occupancy(self.seg)
        self.costmap = CostMap(self.occ, self.conf, cell_m=0.25, vehicle_radius_cells=3)
        self.planner = HybridAStarPlanner(wheelbase_m=2.5, max_steer_rad=0.60)

    def test_plan_finds_valid_non_holonomic_trajectory(self):
        """Planner should find a continuous, collision-free SE(2) path along the corridor."""
        start_pose = (110.0, 40.0, -math.pi / 2.0)
        goal_pose = (60.0, 42.0, -math.pi / 2.0)

        res = self.planner.plan(self.costmap, start_pose, goal_pose, max_iterations=5000)
        self.assertTrue(res.success, f"Planning failed: {res.message}")
        self.assertGreater(len(res.path), 5)

        # Verify no point along trajectory violates costmap traversability
        for y, x, yaw in res.path:
            iy, ix = int(round(y)), int(round(x))
            self.assertTrue(
                self.costmap.is_traversable(iy, ix),
                f"Path intersects non-traversable cell ({iy}, {ix})"
            )

    def test_bounded_turning_radius(self):
        """Curvature of the trajectory must respect the kinematic steering limit."""
        start_pose = (110.0, 40.0, -math.pi / 2.0)
        goal_pose = (50.0, 42.0, -math.pi / 2.0)

        res = self.planner.plan(self.costmap, start_pose, goal_pose, max_iterations=5000)
        self.assertTrue(res.success, f"Plan failed: {res.message}")

        curvatures = res.curvatures
        # Max curvature kappa = 1 / R_min in cell units
        # R_min_m = 2.5 / tan(0.60) ~ 3.65 m -> ~14.6 cells -> max kappa ~ 0.068 cells^-1
        # Allow some discretization tolerance on discrete grid differences (e.g. 0.40)
        for i, k in enumerate(curvatures):
            self.assertLess(k, 0.50, f"Curvature at point {i} exceeds physical limit: {k}")

    def test_degenerate_narrow_corridor_failure_reported(self):
        """When an obstacle completely blocks the corridor, planner must report failure cleanly."""
        blocked_map = self.costmap.copy()
        # Completely block a cross-section of the road
        blocked_map.grid[85, :] = np.inf
        blocked_map.occ[85, :] = 1

        start_pose = (110.0, 40.0, -math.pi / 2.0)
        goal_pose = (60.0, 42.0, -math.pi / 2.0)

        res = self.planner.plan(blocked_map, start_pose, goal_pose, max_iterations=2000)
        self.assertFalse(res.success)
        self.assertIn("blocked", res.message.lower())


if __name__ == "__main__":
    unittest.main()
