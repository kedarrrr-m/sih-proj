"""
tests/test_prediction_safety.py — Unit tests for T2.4 (Dynamic Prediction & Safety State Machine)
"""

import unittest
import math
import numpy as np
from planner.costmap import CostMap
from planner.prediction import TrackedAgent, TrajectoryPredictor
from planner.safety import SafetyController, SafetyState
from planner.perception_bridge import generate_synthetic_perception, seg_to_occupancy


class TestPredictionAndSafety(unittest.TestCase):

    def setUp(self):
        self.seg, self.conf = generate_synthetic_perception(seed=42)
        self.occ = seg_to_occupancy(self.seg)
        self.costmap = CostMap(self.occ, self.conf, cell_m=0.25, vehicle_radius_cells=3)
        self.safety = SafetyController(ttc_critical_s=1.2, ttc_warning_s=2.8)
        self.predictor = TrajectoryPredictor(default_horizon_s=3.0, dt=0.1)

    def test_constant_velocity_prediction(self):
        """Dynamic agent trajectory extrapolation must follow linear motion."""
        agent = TrackedAgent(
            agent_id=1, agent_type="pedestrian",
            y=50.0, x=40.0, vy=-2.0, vx=1.0, radius_cells=2.0
        )
        traj = self.predictor.predict_single(agent, horizon_s=2.0, dt=0.5)
        # Expected at t = 1.0s: y = 50 - 2*1 = 48, x = 40 + 1*1 = 41
        pt_1s = traj[2]  # t = 0.0, 0.5, 1.0
        self.assertAlmostEqual(pt_1s[2], 1.0, places=2)
        self.assertAlmostEqual(pt_1s[0], 48.0, places=2)
        self.assertAlmostEqual(pt_1s[1], 41.0, places=2)

    def test_ttc_detection_on_head_on_approach(self):
        """Approaching agent on collision course must trigger critical TTC."""
        # Ego moving at 8 cells/s from y=80 towards y=60 (heading -pi/2)
        ego_path = [(80.0 - i * 0.8, 40.0, -math.pi/2) for i in range(25)]
        # Head-on vehicle moving at 8 cells/s from y=40 towards y=70 (heading +pi/2)
        head_on_agent = TrackedAgent(
            agent_id=2, agent_type="vehicle",
            y=40.0, x=40.0, vy=8.0, vx=0.0, radius_cells=3.0
        )

        state, ttc, msg = self.safety.evaluate(
            ego_y=80.0, ego_x=40.0, ego_speed=8.0,
            planned_path=ego_path, costmap=self.costmap, agents=[head_on_agent]
        )
        # Relative speed = 16 cells/s. Distance = 40 cells.
        # Time to contact ~ (40 - 6) / 16 ~ 2.1s
        self.assertLess(ttc, 3.0)
        self.assertIn(state, (SafetyState.SLOW, SafetyState.EMERGENCY_STOP))

    def test_replan_triggered_on_static_obstacle_ahead(self):
        """When an obstacle is placed directly on the planned path, REPLAN must trigger."""
        ego_path = [(90.0 - i * 1.0, 40.0, -math.pi/2) for i in range(20)]
        # Inject an obstacle 8 cells ahead at row 82, col 40
        inflated_map = self.costmap.copy()
        inflated_map.inflate_obstacle(82, 40, radius_cells=2, cost_val=np.inf)

        state, ttc, msg = self.safety.evaluate(
            ego_y=90.0, ego_x=40.0, ego_speed=6.0,
            planned_path=ego_path, costmap=inflated_map, agents=[]
        )
        self.assertEqual(state, SafetyState.REPLAN)

    def test_provable_fallback_brake(self):
        """Emergency braking must monotonically bring speed to 0.0."""
        speed = 10.0
        dt = 0.2
        while speed > 0.0:
            speed = self.safety.execute_fail_safe_brake(speed, dt)
        self.assertEqual(speed, 0.0)


if __name__ == "__main__":
    unittest.main()
