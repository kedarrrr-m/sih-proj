from enum import Enum
import numpy as np
from planner.prediction import TrackedAgent

class BehaviourClass(Enum):
    CAUTIOUS = 1
    NORMAL = 2
    AGGRESSIVE = 3

def classify_behaviour(agent: TrackedAgent, history_window: int = 10) -> BehaviourClass:
    """
    Classify agent behaviour as cautious, normal, or aggressive based on its history.
    """
    if not hasattr(agent, 'history') or not agent.history or len(agent.history) < 2:
        return BehaviourClass.NORMAL
        
    history = agent.history[-history_window:]
    if len(history) < 2:
        return BehaviourClass.NORMAL
        
    # history is assumed to be list of dicts or objects with y, x, speed, heading
    # let's assume it's list of dicts with 'vy', 'vx', 'y', 'x' or similar.
    # To be generic, let's extract speeds
    speeds = []
    headings = []
    ys = []
    xs = []
    
    for state in history:
        if isinstance(state, dict):
            vy = state.get('vy', 0.0)
            vx = state.get('vx', 0.0)
            y = state.get('y', 0.0)
            x = state.get('x', 0.0)
        else:
            vy = getattr(state, 'vy', 0.0)
            vx = getattr(state, 'vx', 0.0)
            y = getattr(state, 'y', 0.0)
            x = getattr(state, 'x', 0.0)
            
        speeds.append(np.hypot(vy, vx))
        headings.append(np.arctan2(vy, vx))
        ys.append(y)
        xs.append(x)
        
    speed_variance = np.var(speeds)
    
    # lateral deviation
    if len(xs) >= 2:
        # simple linear fit to path to find lateral deviation
        # For simplicity, just use std dev of headings
        pass
        
    heading_change_rate = np.mean(np.abs(np.diff(np.unwrap(headings))))
    
    if speed_variance < 0.1 and heading_change_rate < 0.1:
        return BehaviourClass.CAUTIOUS
    elif speed_variance > 1.0 or heading_change_rate > 0.5:
        return BehaviourClass.AGGRESSIVE
    else:
        return BehaviourClass.NORMAL

def compute_behaviour_cost(agents: list, costmap_shape: tuple, cell_m: float = 0.25) -> np.ndarray:
    """
    Returns an extra_cost array inflating agent footprints based on behaviour.
    """
    H, W = costmap_shape
    cost = np.zeros((H, W), dtype=float)
    
    for agent in agents:
        b_class = classify_behaviour(agent)
        
        multiplier = 1.5 # NORMAL
        if b_class == BehaviourClass.CAUTIOUS:
            multiplier = 1.0
        elif b_class == BehaviourClass.AGGRESSIVE:
            multiplier = 2.5
            
        base_radius = getattr(agent, 'radius_cells', 2.0)
        inflated_radius = int(np.ceil(base_radius * multiplier))
        
        y, x = int(getattr(agent, 'y', 0)), int(getattr(agent, 'x', 0))
        
        y_min = max(0, y - inflated_radius)
        y_max = min(H, y + inflated_radius + 1)
        x_min = max(0, x - inflated_radius)
        x_max = min(W, x + inflated_radius + 1)
        
        for iy in range(y_min, y_max):
            for ix in range(x_min, x_max):
                if np.hypot(iy - y, ix - x) <= inflated_radius:
                    cost[iy, ix] += 5.0 # Elevate cost
                    
    return cost
