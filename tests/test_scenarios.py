import unittest
import numpy as np
from planner.scenarios import (
    get_base_scenarios, get_all_scenarios, apply_weather, ScenarioRunner
)

class TestScenarios(unittest.TestCase):
    def test_scenario_definitions_complete(self):
        base_scenarios = get_base_scenarios()
        self.assertEqual(len(base_scenarios), 5)
        categories = set(s.category for s in base_scenarios)
        self.assertTrue({"pedestrian", "cyclist", "jaywalker", "wrong_way", "animal"}.issubset(categories))
        
        for sc in base_scenarios:
            self.assertTrue(sc.name)
            self.assertTrue(sc.description)
            self.assertTrue(sc.category)
            self.assertEqual(sc.weather, "clear")
            self.assertTrue(callable(sc.setup))
            
    def test_weather_variants_reduce_confidence(self):
        conf = np.ones((100, 100), dtype=np.float32)
        
        conf_rain = apply_weather(conf, "rain")
        self.assertTrue(np.all(conf_rain < conf))
        self.assertAlmostEqual(conf_rain[0, 0], 0.8)
        
        conf_fog = apply_weather(conf, "fog")
        self.assertTrue(np.all(conf_fog < conf))
        self.assertAlmostEqual(conf_fog[0, 0], 0.5)
        
        conf_night = apply_weather(conf, "night")
        # Night reduces far field (y=0) more than near field
        self.assertTrue(np.all(conf_night < conf))
        self.assertLess(conf_night[0, 0], conf_night[-1, 0])
        
    def test_scenario_runner_single(self):
        base_scenarios = get_base_scenarios()
        ped_scen = next(s for s in base_scenarios if s.name == "pedestrian_from_behind_parked_car")
        
        runner = ScenarioRunner(max_steps=10) # very short run to just test keys
        metrics = runner.run(ped_scen)
        
        expected_keys = {
            "collision_count", "route_completed", "min_ttc", "hard_brake_count",
            "max_curvature", "mean_jerk", "replan_latency_ms", "replan_count",
            "avg_speed_cells_per_s", "speed_vs_confidence", "speed_vs_occlusion",
            "start_dist", "final_dist", "wrong_lane_steps"
        }
        self.assertTrue(expected_keys.issubset(metrics.keys()))
        
    def test_metrics_no_collision_on_safe_scenario(self):
        # The default basic pedestrian scenario where ego starts far away
        # should result in 0 collisions if the safety controller and planner work
        base_scenarios = get_base_scenarios()
        ped_scen = next(s for s in base_scenarios if s.name == "pedestrian_from_behind_parked_car")
        
        runner = ScenarioRunner(max_steps=50) # run for a bit
        metrics = runner.run(ped_scen)
        
        self.assertEqual(metrics["collision_count"], 0)

if __name__ == "__main__":
    unittest.main()
