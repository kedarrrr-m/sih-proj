#!/usr/bin/env python3
"""
================================================================================
 bridge_starter.py  —  SIH 26037/26038  —  Perception -> Planning bridge (MVP)
================================================================================

WHAT THIS IS
------------
The single missing piece in the project bible's Gap 1: the code that turns a
segmentation map into a driven, replanned trajectory. It is deliberately
*standalone and runnable* with a FAKE perception upstream, so you can build and
debug the planner today, before FusionSegNet is wired in.

THE PIPELINE (matches Part VII / VII-B of the bible)
----------------------------------------------------
   fake segmentation + confidence   (stand-in for FusionSegNet)
        -> BEV occupancy grid
        -> cost map   [ obstacle inflation (EDT) + UNCERTAINTY term = Idea B ]
        -> A* global plan            (swap in PythonRobotics Hybrid A* later)
        -> drive along path, detect a blocking obstacle within ObstacleDistance
        -> bump that region's cost and REPLAN   (this is your adaptive loop)

Only deps: numpy, scipy, matplotlib.  Run:  python3 bridge_starter.py
Outputs a figure: bridge_demo.png

WHERE THE REAL SYSTEM PLUGS IN  (search for the tag  # >>> SWAP:  )
-------------------------------------------------------------------
  # >>> SWAP 1 : replace make_fake_perception() with FusionSegNet mask+confidence
  # >>> SWAP 2 : replace the toy A* with PythonRobotics hybrid_a_star_planning()
  # >>> SWAP 3 : behaviour/occlusion cost (Ideas A & C) add into build_cost_map()
================================================================================
"""

import numpy as np
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use("Agg")            # headless; writes a PNG
import matplotlib.pyplot as plt
import heapq

# ----------------------------------------------------------------------------
# Class ids — must match FusionSegNet's 5-class scheme
# ----------------------------------------------------------------------------
BACKGROUND, ROAD, SIDEWALK, VEHICLE, HUMAN = 0, 1, 2, 3, 4

GRID_H, GRID_W = 120, 80          # BEV grid cells (ego frame, top-down)
CELL_M = 0.25                     # metres per cell -> 30 m x 20 m window


# ----------------------------------------------------------------------------
# >>> SWAP 1 : fake perception.  Returns a BEV semantic map + a per-cell
#             confidence map in [0,1].  FusionSegNet gives you exactly these
#             two arrays (after IPM to BEV) — same shapes, real values.
# ----------------------------------------------------------------------------
def make_fake_perception(seed=0):
    rng = np.random.default_rng(seed)
    seg = np.full((GRID_H, GRID_W), BACKGROUND, dtype=np.int8)

    # a drivable road corridor down the middle, edges a bit ragged (unstructured!)
    for y in range(GRID_H):
        cx = GRID_W // 2 + int(6 * np.sin(y / 25.0))
        half = 12 + int(3 * np.sin(y / 9.0))
        seg[y, max(0, cx - half):min(GRID_W, cx + half)] = ROAD
        # sidewalks flanking the road
        seg[y, max(0, cx - half - 3):max(0, cx - half)] = SIDEWALK
        seg[y, min(GRID_W, cx + half):min(GRID_W, cx + half + 3)] = SIDEWALK

    # a couple of static vehicles parked in the corridor
    seg[70:78, 44:52] = VEHICLE
    seg[30:36, 30:37] = VEHICLE

    # confidence: high on clean road, low near class boundaries & far away (noisy)
    conf = np.full((GRID_H, GRID_W), 0.9, dtype=np.float32)
    edges = np.abs(np.gradient(seg.astype(float))[0]) + \
            np.abs(np.gradient(seg.astype(float))[1])
    conf[edges > 0] = 0.4                       # boundaries are uncertain
    conf[:20, :] = 0.5                          # far field (top rows) less certain
    conf += rng.normal(0, 0.03, conf.shape)
    conf = np.clip(conf, 0.05, 1.0)
    return seg, conf


# ----------------------------------------------------------------------------
#  Segmentation -> occupancy.  Road = free, everything else = obstacle.
# ----------------------------------------------------------------------------
def seg_to_occupancy(seg):
    occ = np.ones_like(seg, dtype=np.uint8)     # 1 = blocked by default
    occ[seg == ROAD] = 0                        # only road is freely drivable
    return occ


# ----------------------------------------------------------------------------
#  Cost map = inflated-obstacle distance field  +  uncertainty penalty (Idea B)
#  This is the heart of the bridge and where your novelty lives.
# ----------------------------------------------------------------------------
def build_cost_map(occ, conf, vehicle_radius_cells=3,
                   uncertainty_weight=6.0, extra_cost=None):
    # --- EDT: distance (in cells) from every free cell to nearest obstacle ---
    free = (occ == 0)
    dist = distance_transform_edt(free)                      # big = safe

    # base cost: cheap far from obstacles, expensive near them; hard-block occupied
    with np.errstate(divide="ignore"):
        proximity_cost = np.where(dist > 0, 1.0 / dist, 0.0)
    base = 1.0 + 10.0 * proximity_cost
    base[dist <= vehicle_radius_cells] = np.inf              # vehicle can't fit
    base[occ == 1] = np.inf                                  # obstacle cells

    # --- Idea B: low confidence -> higher cost (drive cautiously where unsure) ---
    uncertainty_cost = uncertainty_weight * (1.0 - conf)

    cost = base + uncertainty_cost
    # >>> SWAP 3 : add behaviour-aware (Idea A) / occlusion (Idea C) costs here:
    if extra_cost is not None:
        cost = cost + extra_cost
    return cost


# ----------------------------------------------------------------------------
# >>> SWAP 2 : toy 8-connected A* on the cost grid.
#   Good enough to see the loop work. For a car-like path with turning radius,
#   replace this whole function with PythonRobotics:
#       from HybridAStar.hybrid_a_star import hybrid_a_star_planning
#       path = hybrid_a_star_planning(start, goal, ox, oy, XY_RES, YAW_RES)
# ----------------------------------------------------------------------------
def astar(cost, start, goal):
    H, W = cost.shape
    if not np.isfinite(cost[start]) or not np.isfinite(cost[goal]):
        return None
    nbrs = [(-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def h(a, b):                                  # octile-ish heuristic
        return np.hypot(a[0] - b[0], a[1] - b[1])

    openq = [(h(start, goal), 0.0, start)]
    came, g = {start: None}, {start: 0.0}
    while openq:
        _, gc, cur = heapq.heappop(openq)
        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur)
                cur = came[cur]
            return path[::-1]
        for dy, dx in nbrs:
            ny, nx = cur[0] + dy, cur[1] + dx
            if 0 <= ny < H and 0 <= nx < W and np.isfinite(cost[ny, nx]):
                step = cost[ny, nx] * (1.41 if dy and dx else 1.0)
                ng = gc + step
                if ng < g.get((ny, nx), np.inf):
                    g[(ny, nx)] = ng
                    came[(ny, nx)] = cur
                    heapq.heappush(openq, (ng + h((ny, nx), goal), ng, (ny, nx)))
    return None


# ----------------------------------------------------------------------------
#  The adaptive loop: drive the path; when a NEW obstacle appears within
#  OBSTACLE_DISTANCE ahead, raise its cost and replan  (mirrors the RoadRunner
#  replanPath mechanism from bible VII-B.2, but continuous, not binary).
# ----------------------------------------------------------------------------
OBSTACLE_DISTANCE_CELLS = 24      # ~6 m look-ahead trigger

def drive_and_replan(cost, path, dynamic_obstacle):
    """Walk along `path`; inject a surprise obstacle; replan around it."""
    oy, ox = dynamic_obstacle                         # a cell that becomes blocked
    for i, (py, px) in enumerate(path):
        if np.hypot(py - oy, px - ox) <= OBSTACLE_DISTANCE_CELLS:
            # perception now sees the obstacle -> bump a region of cost, replan
            new_cost = cost.copy()
            yy, xx = np.ogrid[:cost.shape[0], :cost.shape[1]]
            blob = (yy - oy) ** 2 + (xx - ox) ** 2 <= 5 ** 2
            new_cost[blob] = np.inf                    # inflate the new obstacle
            replanned = astar(new_cost, (py, px), path[-1])
            return i, new_cost, replanned
    return len(path) - 1, cost, None


# ----------------------------------------------------------------------------
#  Run it end to end and draw the result.
# ----------------------------------------------------------------------------
def main():
    seg, conf = make_fake_perception()
    occ = seg_to_occupancy(seg)
    cost = build_cost_map(occ, conf)

    start = (GRID_H - 5, GRID_W // 2)                 # ego, bottom-centre
    goal = (5, GRID_W // 2)                           # far end of corridor
    path = astar(cost, start, goal)
    assert path, "No initial path found — check the fake map."

    # a pedestrian steps out from behind the parked car, mid-corridor
    surprise = (55, 46)
    trigger_i, cost2, replanned = drive_and_replan(cost, path, surprise)

    # ----- visualise -----
    fig, ax = plt.subplots(1, 3, figsize=(15, 7))

    ax[0].imshow(seg, cmap="tab10", origin="lower", vmin=0, vmax=9)
    ax[0].set_title("1. Perception (fake FusionSegNet)\nBEV semantic map")

    finite = np.isfinite(cost)
    show = np.where(finite, cost, np.nan)
    im = ax[1].imshow(show, cmap="viridis", origin="lower")
    ax[1].set_title("2. Cost map\n(obstacle EDT + uncertainty, Idea B)")
    fig.colorbar(im, ax=ax[1], fraction=0.046)

    ax[2].imshow(show, cmap="viridis", origin="lower", alpha=0.6)
    py, px = zip(*path)
    ax[2].plot(px, py, "w--", lw=2, label="original plan")
    if replanned:
        ry, rx = zip(*replanned)
        ax[2].plot(rx, ry, "r-", lw=2.5, label="replanned")
    ax[2].plot(surprise[1], surprise[0], "rx", ms=14, mew=3, label="pedestrian")
    ax[2].plot(start[1], start[0], "bo", ms=8, label="ego")
    ax[2].plot(goal[1], goal[0], "g*", ms=14, label="goal")
    ax[2].legend(loc="upper right", fontsize=8)
    ax[2].set_title("3. Plan -> replan on hazard\n(adaptive avoidance loop)")

    for a in ax:
        a.set_xticks([]); a.set_yticks([])
    plt.tight_layout()
    plt.savefig("bridge_demo.png", dpi=110, bbox_inches="tight")
    print("Wrote bridge_demo.png")
    print(f"  initial path length : {len(path)} cells")
    print(f"  replan triggered at step {trigger_i} "
          f"({'replanned OK' if replanned else 'no detour found'})")
    if replanned:
        print(f"  replanned path length: {len(replanned)} cells")


if __name__ == "__main__":
    main()
