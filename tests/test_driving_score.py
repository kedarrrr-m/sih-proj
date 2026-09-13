import unittest
from planner.driving_score import route_completion, infraction_penalty, driving_score, compute_suite_scores

class TestDrivingScore(unittest.TestCase):
    def test_perfect_run(self):
        comp = route_completion(0.0, 100.0)
        pen = infraction_penalty(collisions=0, hard_brakes=0, wrong_lane_steps=0)
        score = driving_score(comp, pen)
        self.assertAlmostEqual(score, 1.0)
        
    def test_collision_penalty(self):
        comp = route_completion(0.0, 100.0)
        pen = infraction_penalty(collisions=1, hard_brakes=0, wrong_lane_steps=0)
        score = driving_score(comp, pen)
        self.assertAlmostEqual(score, 0.5)
        
    def test_partial_route(self):
        comp = route_completion(50.0, 100.0)
        pen = infraction_penalty(collisions=1, hard_brakes=0)
        score = driving_score(comp, pen)
        self.assertAlmostEqual(score, 0.25)
        
    def test_suite_aggregation(self):
        results = [
            {"start_dist": 100.0, "final_dist": 0.0, "route_completed": True, "collision_count": 0, "hard_brake_count": 0},
            {"start_dist": 100.0, "final_dist": 50.0, "route_completed": False, "collision_count": 1, "hard_brake_count": 0},
        ]
        agg = compute_suite_scores(results)
        self.assertAlmostEqual(agg["average_driving_score"], 0.625)

if __name__ == "__main__":
    unittest.main()
