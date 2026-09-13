from typing import List, Dict

def route_completion(ego_final_dist: float, start_dist: float) -> float:
    """Calculate the route completion percentage (0.0 to 1.0)."""
    if start_dist <= 0:
        return 1.0
    # The ego_final_dist is the remaining distance to the goal.
    # If final is > start, progress is 0.
    progress = start_dist - ego_final_dist
    return max(0.0, min(1.0, progress / start_dist))

def infraction_penalty(collisions: int, hard_brakes: int, wrong_lane_steps: int = 0) -> float:
    """Calculate the multiplicative penalty for infractions."""
    penalty = 1.0
    penalty *= (0.5 ** collisions)
    penalty *= (0.95 ** hard_brakes)
    # Could add wrong lane penalty if defined, e.g., 0.99 ** wrong_lane_steps
    return max(0.0, penalty)

def driving_score(route_completion_val: float, infraction_penalty_val: float) -> float:
    """Calculate the final driving score."""
    return route_completion_val * infraction_penalty_val

def compute_suite_scores(scenario_results: List[Dict]) -> Dict:
    """Aggregate scores across a suite of scenario runs."""
    total_score = 0.0
    details = []
    
    for res in scenario_results:
        start_dist = res.get('start_dist', 100.0)
        final_dist = res.get('final_dist', 0.0)
        collisions = res.get('collision_count', 0)
        hard_brakes = res.get('hard_brake_count', 0)
        wrong_lane = res.get('wrong_lane_steps', 0)
        
        comp = route_completion(final_dist, start_dist)
        if res.get('route_completed', False):
            comp = 1.0
            
        pen = infraction_penalty(collisions, hard_brakes, wrong_lane)
        score = driving_score(comp, pen)
        
        details.append(score)
        total_score += score
        
    avg_score = total_score / max(1, len(scenario_results)) if scenario_results else 0.0
    return {
        "average_driving_score": avg_score,
        "total_scenarios": len(scenario_results),
        "scores_per_scenario": details
    }
