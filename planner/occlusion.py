import numpy as np
from planner.prediction import TrackedAgent

def compute_occlusion_mask(occ: np.ndarray, ego_y: int, ego_x: int, num_rays: int = 180) -> np.ndarray:
    """
    Compute an occlusion mask using ray-casting from the ego position.
    """
    H, W = occ.shape
    mask = np.zeros((H, W), dtype=bool)
    angles = np.linspace(0, 2 * np.pi, num_rays, endpoint=False)
    
    max_dist = int(np.ceil(np.sqrt(H**2 + W**2)))
    
    for angle in angles:
        dy = np.sin(angle)
        dx = np.cos(angle)
        
        hit_obstacle = False
        
        for r in range(1, max_dist):
            y = int(np.round(ego_y + r * dy))
            x = int(np.round(ego_x + r * dx))
            
            if y < 0 or y >= H or x < 0 or x >= W:
                break
                
            if hit_obstacle:
                mask[y, x] = True
            elif occ[y, x] == 1:
                hit_obstacle = True
                
    return mask

def place_phantom_agents(occlusion_mask: np.ndarray, occ: np.ndarray, ego_y: int, ego_x: int, phantom_speed_cells: float = 4.0, phantom_radius: int = 3):
    """
    Place phantom agents at the boundary between visible and occluded regions adjacent to obstacles.
    """
    H, W = occlusion_mask.shape
    phantoms = []
    
    boundary_mask = np.zeros_like(occlusion_mask)
    for y in range(1, H-1):
        for x in range(1, W-1):
            if occlusion_mask[y, x] and occ[y, x] == 0:
                if (occ[y-1, x] == 1 or occ[y+1, x] == 1 or occ[y, x-1] == 1 or occ[y, x+1] == 1):
                    boundary_mask[y, x] = True
                        
    coords = np.argwhere(boundary_mask)
    if len(coords) > 0:
        for i in range(0, len(coords), max(1, len(coords)//5)):
            y, x = coords[i]
            dy = ego_y - y
            dx = ego_x - x
            dist = np.hypot(dy, dx)
            if dist > 0:
                vy = (dy / dist) * phantom_speed_cells
                vx = (dx / dist) * phantom_speed_cells
            else:
                vy, vx = 0.0, 0.0
                
            agent = TrackedAgent(agent_id=9000 + len(phantoms), agent_type="pedestrian", y=float(y), x=float(x), vy=vy, vx=vx, radius_cells=float(phantom_radius))
            phantoms.append(agent)
            
    return phantoms

def compute_occlusion_cost(occ: np.ndarray, conf, ego_y: int, ego_x: int, occlusion_weight: float = 8.0) -> np.ndarray:
    """
    Returns an extra_cost array where occluded cells near obstacles get a high penalty.
    """
    H, W = occ.shape
    mask = compute_occlusion_mask(occ, ego_y, ego_x)
    
    cost = np.zeros((H, W), dtype=float)
    
    boundary_mask = np.zeros_like(mask)
    for y in range(1, H-1):
        for x in range(1, W-1):
            if mask[y, x] and occ[y, x] == 0:
                if (occ[y-1, x] == 1 or occ[y+1, x] == 1 or occ[y, x-1] == 1 or occ[y, x+1] == 1):
                    boundary_mask[y, x] = True
                    
    coords = np.argwhere(boundary_mask)
    from scipy.ndimage import distance_transform_edt
    dist_to_boundary = distance_transform_edt(~boundary_mask)
    cost = np.where(mask, occlusion_weight * np.exp(-dist_to_boundary / 5.0), 0.0)
    return cost.astype(float)
