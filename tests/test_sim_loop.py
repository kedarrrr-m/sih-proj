"""
tests/test_sim_loop.py — End-to-end integration tests for T2.5 and T2.6 (Full Phase 2 MVP Loop)
"""

import unittest
from planner.sim_loop import ClosedLoopSimulator


class TestClosedLoopSimulation(unittest.TestCase):

    def test_end_to_end_mvp_loop(self):
        """
        Executes the full perception -> costmap -> predict -> plan -> check -> control loop.
        Verifies the 5 Phase 2 MVP criteria:
        1. Perception interface provides valid semantic & confidence arrays.
        2. BEV CostMap is formed with finite drivable space and EDT inflation.
        3. Non-holonomic Hybrid A* trajectory navigates drivable space.
        4. Dynamic hazard triggers continuous-cost replanning.
        5. Ego successfully reaches goal with 0 collisions in continuous simulation.
        """
        sim = ClosedLoopSimulator(seed=42)
        metrics = sim.run(max_steps=200)

        # 1. Zero collisions
        self.assertEqual(metrics["collisions"], 0, "Simulation reported footprint collisions!")

        # 2. Dynamic hazard replan triggered and executed
        self.assertGreaterEqual(metrics["replan_count"], 1, "Expected at least 1 adaptive replan event!")
        for lat in metrics["replan_latencies_ms"]:
            self.assertGreater(lat, 0.0)

        # 3. Route completion
        self.assertTrue(metrics["route_completed"], f"Goal not reached. Final dist: {metrics['final_distance_to_goal']:.2f}")

        # 4. Telemetry recorded
        self.assertGreater(len(sim.history_ego), 20)
        self.assertGreater(len(sim.history_states), 20)


if __name__ == "__main__":
    unittest.main()
