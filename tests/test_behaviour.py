import unittest
import numpy as np
from planner.behaviour import BehaviourClass, classify_behaviour, compute_behaviour_cost

class DummyTrackedAgent:
    def __init__(self, y, x, history, radius=2.0):
        self.y = y
        self.x = x
        self.history = history
        self.radius = radius

class TestBehaviour(unittest.TestCase):
    def test_stationary_agent_is_cautious(self):
        history = [{'vy': 0.0, 'vx': 0.0} for _ in range(10)]
        agent = DummyTrackedAgent(10, 10, history)
        self.assertEqual(classify_behaviour(agent), BehaviourClass.CAUTIOUS)
        
    def test_erratic_agent_is_aggressive(self):
        history = []
        for i in range(10):
            vy = 2.0 if i % 2 == 0 else -2.0
            vx = 2.0 if i % 2 == 0 else -2.0
            history.append({'vy': vy, 'vx': vx})
        agent = DummyTrackedAgent(10, 10, history)
        self.assertEqual(classify_behaviour(agent), BehaviourClass.AGGRESSIVE)
        
    def test_behaviour_cost_wider_berth_for_aggressive(self):
        cautious_agent = DummyTrackedAgent(10, 10, [{'vy': 0.0, 'vx': 0.0} for _ in range(10)], radius=2)
        
        agg_history = []
        for i in range(10):
            vy = 2.0 if i % 2 == 0 else -2.0
            vx = 2.0 if i % 2 == 0 else -2.0
            agg_history.append({'vy': vy, 'vx': vx})
        agg_agent = DummyTrackedAgent(10, 10, agg_history, radius=2)
        
        cost_cautious = compute_behaviour_cost([cautious_agent], (20, 20))
        cost_agg = compute_behaviour_cost([agg_agent], (20, 20))
        
        cautious_area = np.sum(cost_cautious > 0)
        agg_area = np.sum(cost_agg > 0)
        self.assertTrue(agg_area > cautious_area)
        
    def test_two_scenes_different_aggression(self):
        cautious_agent = DummyTrackedAgent(10, 10, [{'vy': 0.0, 'vx': 0.0} for _ in range(10)])
        agg_history = [{'vy': 5.0 if i % 2 == 0 else 0.0, 'vx': 0.0} for i in range(10)]
        agg_agent = DummyTrackedAgent(10, 10, agg_history)
        
        cost1 = compute_behaviour_cost([cautious_agent], (20, 20))
        cost2 = compute_behaviour_cost([agg_agent], (20, 20))
        
        self.assertFalse(np.array_equal(cost1, cost2))

if __name__ == '__main__':
    unittest.main()
