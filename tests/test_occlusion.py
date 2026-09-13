import unittest
import numpy as np
import sys

# Mock TrackedAgent if needed for tests
class MockTrackedAgent:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
import planner
if not hasattr(planner, 'prediction'):
    class MockPrediction:
        TrackedAgent = MockTrackedAgent
    planner.prediction = MockPrediction()
    sys.modules['planner.prediction'] = planner.prediction

from planner.occlusion import compute_occlusion_mask, place_phantom_agents, compute_occlusion_cost

class TestOcclusion(unittest.TestCase):
    def setUp(self):
        self.occ = np.zeros((20, 20), dtype=int)
        self.ego_y, self.ego_x = 10, 10
        
    def test_occlusion_behind_obstacle(self):
        self.occ[10, 13] = 1 # obstacle to the right
        mask = compute_occlusion_mask(self.occ, self.ego_y, self.ego_x)
        self.assertTrue(mask[10, 14])
        self.assertTrue(mask[10, 15])
        self.assertFalse(mask[10, 12])
        self.assertFalse(mask[10, 9])
        
    def test_phantom_placement_at_occlusion_boundary(self):
        self.occ[10, 13] = 1
        mask = compute_occlusion_mask(self.occ, self.ego_y, self.ego_x)
        phantoms = place_phantom_agents(mask, self.occ, self.ego_y, self.ego_x)
        self.assertTrue(len(phantoms) > 0)
        
    def test_occlusion_cost_highest_near_boundary(self):
        self.occ[10, 13] = 1
        conf = None
        cost = compute_occlusion_cost(self.occ, conf, self.ego_y, self.ego_x)
        self.assertTrue(cost[10, 14] > cost[10, 18])
        
    def test_no_occlusion_in_clear_field(self):
        mask = compute_occlusion_mask(self.occ, self.ego_y, self.ego_x)
        self.assertFalse(np.any(mask))
        
if __name__ == '__main__':
    unittest.main()
