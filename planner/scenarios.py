import time
from typing import Callable, List, Tuple, Dict
from dataclasses import dataclass
import numpy as np

from planner.perception_bridge import (
    generate_synthetic_perception, seg_to_occupancy, ROAD, VEHICLE, HUMAN, BACKGROUND, SIDEWALK, GRID_H, GRID_W, CELL_M
)
from planner.costmap import CostMap
from planner.hybrid_a_star import HybridAStarPlanner, PlanResult
from planner.prediction import TrackedAgent
from planner.safety import SafetyController, SafetyState

@dataclass
class Scenario:
    name: str
    description: str
    category: str
    weather: str
    setup: Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, List[TrackedAgent], Tuple[float,float,float], Tuple[float,float,float]]]

def apply_weather(conf: np.ndarray, weather: str) -> np.ndarray:
    mod_conf = conf.copy()
    if weather == "rain":
        mod_conf = mod_conf * 0.8
    elif weather == "fog":
        mod_conf = mod_conf * 0.5
    elif weather == "night":
        grid_h = conf.shape[0]
        y_coords = np.arange(grid_h).reshape(-1, 1)
        # Assuming y=0 is far field, lower confidence at top
        penalty = 0.4 + 0.6 * (y_coords / grid_h)
        mod_conf = mod_conf * penalty
    return np.clip(mod_conf, 0.0, 1.0)

def setup_pedestrian_from_behind_parked_car(seg, conf):
    seg_mod = seg.copy()
    conf_mod = conf.copy()
    # Parked car at row 70-78, col 44-52
    seg_mod[70:78, 44:52] = VEHICLE
    agents = [
        TrackedAgent(agent_id=1, agent_type="pedestrian", y=74.0, x=48.0, vy=0.0, vx=-2.0, radius_cells=1.5)
    ]
    return seg_mod, conf_mod, agents, (110.0, 40.0, -np.pi/2), (15.0, 40.0, -np.pi/2)

def setup_cyclist_crossing(seg, conf):
    agents = [
        TrackedAgent(agent_id=1, agent_type="cyclist", y=65.0, x=30.0, vy=-1.0, vx=2.5, radius_cells=1.8)
    ]
    return seg, conf, agents, (110.0, 40.0, -np.pi/2), (15.0, 40.0, -np.pi/2)

def setup_jaywalker_mid_corridor(seg, conf):
    agents = [
        TrackedAgent(agent_id=1, agent_type="pedestrian", y=55.0, x=48.0, vy=0.0, vx=-2.0, radius_cells=1.5)
    ]
    return seg, conf, agents, (110.0, 40.0, -np.pi/2), (15.0, 40.0, -np.pi/2)

def setup_wrong_way_vehicle(seg, conf):
    agents = [
        TrackedAgent(agent_id=1, agent_type="vehicle", y=50.0, x=38.0, vy=3.0, vx=0.0, radius_cells=2.5)
    ]
    return seg, conf, agents, (110.0, 40.0, -np.pi/2), (15.0, 40.0, -np.pi/2)

def setup_animal_crossing(seg, conf):
    agents = [
        TrackedAgent(agent_id=1, agent_type="animal", y=80.0, x=32.0, vy=0.0, vx=1.2, radius_cells=1.2)
    ]
    return seg, conf, agents, (110.0, 40.0, -np.pi/2), (15.0, 40.0, -np.pi/2)

def get_base_scenarios() -> List[Scenario]:
    return [
        Scenario("pedestrian_from_behind_parked_car", "Pedestrian stepping out", "pedestrian", "clear", setup_pedestrian_from_behind_parked_car),
        Scenario("cyclist_crossing", "Cyclist crossing diagonally", "cyclist", "clear", setup_cyclist_crossing),
        Scenario("jaywalker_mid_corridor", "Pedestrian entering road suddenly", "jaywalker", "clear", setup_jaywalker_mid_corridor),
        Scenario("wrong_way_vehicle", "Vehicle driving wrong way", "wrong_way", "clear", setup_wrong_way_vehicle),
        Scenario("animal_crossing", "Small slow animal crossing", "animal", "clear", setup_animal_crossing),
    ]

def get_all_scenarios() -> List[Scenario]:
    base = get_base_scenarios()
    all_scenarios = []
    weathers = ["clear", "rain", "fog", "night"]
    for sc in base:
        for w in weathers:
            all_scenarios.append(Scenario(
                name=f"{sc.name}_{w}",
                description=f"{sc.description} in {w}",
                category=sc.category,
                weather=w,
                setup=sc.setup
            ))
    return all_scenarios

class ScenarioRunner:
    def __init__(self, step_dt: float = 0.1, max_steps: int = 150):
        self.step_dt = step_dt
        self.max_steps = max_steps
        
    def run(self, scenario: Scenario) -> Dict:
        # Generate base synthetic map
        seg, conf = generate_synthetic_perception()
        
        # Scenario setup
        seg, conf, agents, start_pose, goal_pose = scenario.setup(seg, conf)
        
        # Apply weather
        conf = apply_weather(conf, scenario.weather)
        
        # Initialize modules
        from planner.occlusion import compute_occlusion_mask, compute_occlusion_cost
        from planner.behaviour import compute_behaviour_cost
        
        occ = seg_to_occupancy(seg)
        # Extra cost from occlusion (Idea C) and dynamic behaviour (Idea A)
        extra_cost = compute_occlusion_cost(occ, conf, int(start_pose[0]), int(start_pose[1]))
        extra_cost += compute_behaviour_cost(agents, (GRID_H, GRID_W))
        costmap = CostMap(occ, conf, extra_cost=extra_cost)
        planner = HybridAStarPlanner()
        safety = SafetyController()
        
        # Ego state
        ego_y, ego_x, ego_yaw = start_pose
        ego_speed = 0.0
        ego_accel = 0.0
        
        metrics = {
            "collision_count": 0,
            "route_completed": False,
            "min_ttc": float('inf'),
            "hard_brake_count": 0,
            "max_curvature": 0.0,
            "mean_jerk": 0.0,
            "replan_latency_ms": [],
            "replan_count": 0,
            "avg_speed_cells_per_s": 0.0,
            "speed_vs_confidence": [],
            "speed_vs_occlusion": [],
            "start_dist": float(np.hypot(goal_pose[0] - start_pose[0], goal_pose[1] - start_pose[1])),
            "final_dist": 0.0,
            "wrong_lane_steps": 0
        }
        
        planned_path = []
        speed_history = []
        accel_history = []
        
        # Initial Plan
        t0 = time.time()
        plan_res = planner.plan(costmap, start_pose, goal_pose)
        t1 = time.time()
        metrics["replan_latency_ms"].append((t1 - t0)*1000)
        if plan_res.success:
            planned_path = list(plan_res.path)
            metrics["replan_count"] += 1
            if plan_res.curvatures:
                metrics["max_curvature"] = float(max(plan_res.curvatures))
            
        for step in range(self.max_steps):
            # Compute adaptivity
            r, c = int(round(ego_y)), int(round(ego_x))
            local_conf = 1.0
            local_occ = 0.0
            if 0 <= r < GRID_H and 0 <= c < GRID_W:
                r_min, r_max = max(0, r-6), min(GRID_H, r+7)
                c_min, c_max = max(0, c-6), min(GRID_W, c+7)
                local_conf = float(np.mean(conf[r_min:r_max, c_min:c_max]))
                local_occ = float(np.mean(extra_cost[r_min:r_max, c_min:c_max] > 0.5))
            metrics["speed_vs_confidence"].append((local_conf, ego_speed))
            metrics["speed_vs_occlusion"].append((local_occ, ego_speed))
            
            # Step agents
            for a in agents:
                a.y += a.vy * self.step_dt
                a.x += a.vx * self.step_dt
                # Check collision with ego
                dist = np.hypot(a.y - ego_y, a.x - ego_x)
                if dist < (a.radius_cells + 1.5):
                    metrics["collision_count"] += 1
            
            # Safety evaluation with occlusion mask
            occ_mask = compute_occlusion_mask(occ, r, c)
            state, min_ttc, _ = safety.evaluate(ego_y, ego_x, ego_speed, planned_path, costmap, agents, occlusion_mask=occ_mask)
            metrics["min_ttc"] = min(metrics["min_ttc"], min_ttc)
            
            # Decide command
            target_accel = 0.0
            if state == SafetyState.CRUISE:
                target_accel = 2.5
            elif state == SafetyState.YIELD:
                target_accel = -2.0
            elif state == SafetyState.SLOW:
                target_accel = -4.5
            elif state in (SafetyState.EMERGENCY_STOP, SafetyState.REPLAN):
                target_accel = -8.0
                if state == SafetyState.REPLAN:
                    t0 = time.time()
                    plan_res = planner.plan(costmap, (ego_y, ego_x, ego_yaw), goal_pose)
                    t1 = time.time()
                    metrics["replan_latency_ms"].append((t1 - t0)*1000)
                    if plan_res.success:
                        planned_path = list(plan_res.path)
                        metrics["replan_count"] += 1
                        if plan_res.curvatures:
                            metrics["max_curvature"] = max(metrics["max_curvature"], float(max(plan_res.curvatures)))
                        
            # Apply kinematics
            jerk = (target_accel - ego_accel) / self.step_dt
            ego_accel = target_accel
            accel_history.append(ego_accel)
            
            if target_accel < -6.0:
                metrics["hard_brake_count"] += 1
                
            ego_speed = max(0.0, min(10.0, ego_speed + ego_accel * self.step_dt))
            speed_history.append(ego_speed)
            
            # Move ego along path
            if ego_speed > 0 and len(planned_path) > 1:
                lookahead = min(len(planned_path) - 1, int(ego_speed * self.step_dt * 2) + 1)
                target_pt = planned_path[lookahead]
                dy = target_pt[0] - ego_y
                dx = target_pt[1] - ego_x
                dist_t = np.hypot(dy, dx)
                
                if dist_t > 0:
                    ego_y += (dy/dist_t) * ego_speed * self.step_dt
                    ego_x += (dx/dist_t) * ego_speed * self.step_dt
                    ego_yaw = np.arctan2(dy, dx)
                    
                # pop visited path
                while len(planned_path) > 1 and np.hypot(planned_path[0][0] - ego_y, planned_path[0][1] - ego_x) < 2.0:
                    planned_path.pop(0)
                    
            # Check goal completion
            dist_to_goal = np.hypot(goal_pose[0] - ego_y, goal_pose[1] - ego_x)
            if dist_to_goal < 5.0:
                metrics["route_completed"] = True
                metrics["final_dist"] = float(dist_to_goal)
                break
                
        metrics["final_dist"] = float(np.hypot(goal_pose[0] - ego_y, goal_pose[1] - ego_x))
        if speed_history:
            metrics["avg_speed_cells_per_s"] = float(np.mean(speed_history))
        if accel_history:
            jerk_vals = np.abs(np.diff(accel_history) / self.step_dt)
            if len(jerk_vals) > 0:
                metrics["mean_jerk"] = float(np.mean(jerk_vals))
                
        return metrics

