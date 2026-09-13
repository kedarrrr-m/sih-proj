"""
tests/test_costmap.py — Unit tests for T2.2 (CostMap with EDT and Idea B Uncertainty)
"""

import unittest
import numpy as np
from planner.costmap import CostMap
from planner.perception_bridge import generate_synthetic_perception, seg_to_occupancy, ROAD


class TestCostMap(unittest.TestCase):

    def setUp(self):
        self.seg, self.conf = generate_synthetic_perception(seed=42)
        self.occ = seg_to_occupancy(self.seg)
        self.costmap = CostMap(self.occ, self.conf, cell_m=0.25, vehicle_radius_cells=3, uncertainty_weight=6.0)

    def test_obstacle_cells_are_infinite(self):
        """All non-road (obstacle) cells must have infinite cost."""
        obs_mask = (self.occ == 1)
        self.assertTrue(np.all(np.isinf(self.costmap.grid[obs_mask])))

    def test_vehicle_radius_inflation(self):
        """Cells within vehicle_radius_cells of any obstacle must be infinite (hard block)."""
        near_mask = (self.costmap.dist <= 3)
        self.assertTrue(np.all(np.isinf(self.costmap.grid[near_mask])))

    def test_drivable_corridor_has_finite_cost(self):
        """The center of the road corridor must be finite and traversable."""
        # Check center row at bottom
        cy, cx = 110, 40
        self.assertTrue(self.costmap.is_traversable(cy, cx))
        self.assertTrue(np.isfinite(self.costmap.get_cost(cy, cx)))

    def test_idea_b_uncertainty_raises_cost(self):
        """Lower confidence must demonstrably raise cost on identical free cells."""
        occ = np.zeros((10, 10), dtype=np.uint8)
        conf_high = np.full((10, 10), 0.95, dtype=np.float32)
        conf_low = np.full((10, 10), 0.20, dtype=np.float32)

        cm_high = CostMap(occ, conf_high, vehicle_radius_cells=0, uncertainty_weight=5.0)
        cm_low = CostMap(occ, conf_low, vehicle_radius_cells=0, uncertainty_weight=5.0)

        # Difference must be exactly uncertainty_weight * (0.95 - 0.20) = 5.0 * 0.75 = 3.75
        expected_diff = 5.0 * (0.95 - 0.20)
        actual_diff = cm_low.get_cost(5, 5) - cm_high.get_cost(5, 5)
        self.assertAlmostEqual(actual_diff, expected_diff, places=4)

    def test_extra_cost_hook(self):
        """SWAP 3 extra_cost hook must add cost without mutating base."""
        occ = np.zeros((10, 10), dtype=np.uint8)
        extra = np.full((10, 10), 12.5, dtype=np.float32)
        cm_base = CostMap(occ, None, vehicle_radius_cells=0)
        cm_extra = CostMap(occ, None, vehicle_radius_cells=0, extra_cost=extra)
        diff = cm_extra.get_cost(5, 5) - cm_base.get_cost(5, 5)
        self.assertAlmostEqual(diff, 12.5, places=3)

    def test_dynamic_inflation(self):
        """inflate_obstacle must mark specified circular region as inf."""
        cy, cx = 50, 40
        self.assertTrue(self.costmap.is_traversable(cy, cx))
        self.costmap.inflate_obstacle(cy, cx, radius_cells=2, cost_val=np.inf)
        self.assertFalse(self.costmap.is_traversable(cy, cx))
        self.assertFalse(self.costmap.is_traversable(cy + 1, cx))


if __name__ == "__main__":
    unittest.main()
