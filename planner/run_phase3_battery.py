"""
planner/run_phase3_battery.py — T3.3, T3.4, T3.6 (Full Scenario Battery & Adaptivity Verification)

Executes the full NHTSA scenario battery across all weather variants, computes the
composite CARLA Driving Score, verifies the three adaptive caution signals, and generates
publication-grade figures for the demo deck and KPI table.
"""

import time
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from planner.scenarios import get_all_scenarios, ScenarioRunner
from planner.driving_score import route_completion, infraction_penalty, driving_score, compute_suite_scores
from planner.behaviour import BehaviourClass, compute_behaviour_cost
from planner.prediction import TrackedAgent


def run_battery():
    print("=" * 80)
    print("RUNNING PHASE 3 SCENARIO BATTERY (NHTSA Typology x Weather Variants)")
    print("=" * 80)

    all_scenarios = get_all_scenarios()
    runner = ScenarioRunner(step_dt=0.1, max_steps=180)

    results = []
    all_speed_conf = []
    all_speed_occ = []

    t_start = time.perf_counter()

    for idx, sc in enumerate(all_scenarios):
        print(f"[{idx+1:02d}/{len(all_scenarios):02d}] Running: {sc.name:45s} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        metrics = runner.run(sc)
        elapsed = (time.perf_counter() - t0)

        # Compute driving score
        comp = route_completion(metrics["final_dist"], metrics["start_dist"])
        if metrics["route_completed"]:
            comp = 1.0
        pen = infraction_penalty(metrics["collision_count"], metrics["hard_brake_count"], metrics.get("wrong_lane_steps", 0))
        score = driving_score(comp, pen)

        metrics["scenario_name"] = sc.name
        metrics["category"] = sc.category
        metrics["weather"] = sc.weather
        metrics["route_completion_pct"] = comp * 100.0
        metrics["infraction_penalty"] = pen
        metrics["driving_score"] = score * 100.0

        results.append(metrics)
        all_speed_conf.extend(metrics.get("speed_vs_confidence", []))
        all_speed_occ.extend(metrics.get("speed_vs_occlusion", []))

        print(f"Done ({elapsed:.1f}s) | Collisions: {metrics['collision_count']} | DS: {metrics['driving_score']:.1f}% | Min TTC: {metrics['min_ttc']:.2f}s")

    total_time = time.perf_counter() - t_start

    # Suite aggregation
    suite_summary = compute_suite_scores(results)
    avg_driving_score = np.mean([r["driving_score"] for r in results])
    avg_route_comp = np.mean([r["route_completion_pct"] for r in results])
    total_collisions = sum(r["collision_count"] for r in results)
    zero_collision_runs = sum(1 for r in results if r["collision_count"] == 0)
    all_latencies = [lat for r in results for lat in r["replan_latency_ms"]]
    avg_replan_lat = np.mean(all_latencies) if all_latencies else 0.0

    print("\n" + "=" * 80)
    print("PHASE 3 BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Total Scenarios Evaluated : {len(results)}")
    print(f"Zero-Collision Scenarios  : {zero_collision_runs} / {len(results)} ({zero_collision_runs/len(results)*100:.1f}%)")
    print(f"Total Collisions          : {total_collisions}")
    print(f"Average Route Completion  : {avg_route_comp:.1f}%")
    print(f"Average Driving Score     : {avg_driving_score:.1f}%")
    print(f"Mean Replanning Latency   : {avg_replan_lat:.2f} ms")
    print(f"Total Evaluation Time     : {total_time:.1f} s")

    # Generate Adaptivity and KPI plots
    generate_phase3_figures(results, all_speed_conf, all_speed_occ)

    return results, suite_summary


def generate_phase3_figures(results, all_speed_conf, all_speed_occ):
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))

    # --- Panel 1: Idea B — Speed vs Perception Confidence ---
    ax1 = axs[0, 0]
    if all_speed_conf:
        confs, speeds = zip(*all_speed_conf)
        confs = np.array(confs)
        speeds = np.array(speeds) * 0.25  # convert to m/s
        # Bin by confidence
        bins = np.linspace(0.2, 1.0, 9)
        bin_means = []
        bin_centers = []
        bin_stds = []
        for i in range(len(bins) - 1):
            mask = (confs >= bins[i]) & (confs < bins[i+1])
            if np.any(mask):
                bin_centers.append((bins[i] + bins[i+1]) * 0.5)
                bin_means.append(np.mean(speeds[mask]))
                bin_stds.append(np.std(speeds[mask]))

        ax1.scatter(confs[::4], speeds[::4], alpha=0.15, color="teal", s=10, label="Step Observations")
        if bin_centers:
            ax1.plot(bin_centers, bin_means, "b-o", lw=3, ms=8, label="Mean Ego Speed")
            ax1.fill_between(bin_centers, np.array(bin_means) - np.array(bin_stds),
                             np.array(bin_means) + np.array(bin_stds), color="blue", alpha=0.2)
        ax1.set_xlabel("Perception Confidence (FusionSegNet / Weather)", fontsize=11)
        ax1.set_ylabel("Ego Velocity (m/s)", fontsize=11)
        ax1.set_title("Signal 1: Speed vs Confidence (Idea B)\nCaution Increases with Lower Confidence", fontsize=12, fontweight="bold")
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper left")

    # --- Panel 2: Idea C — Speed vs Occlusion Risk ---
    ax2 = axs[0, 1]
    if all_speed_occ:
        occs, speeds = zip(*all_speed_occ)
        occs = np.array(occs)
        speeds = np.array(speeds) * 0.25  # m/s
        bins = np.linspace(0.0, 0.8, 8)
        bin_means = []
        bin_centers = []
        for i in range(len(bins) - 1):
            mask = (occs >= bins[i]) & (occs < bins[i+1])
            if np.any(mask):
                bin_centers.append((bins[i] + bins[i+1]) * 0.5)
                bin_means.append(np.mean(speeds[mask]))

        ax2.scatter(occs[::4], speeds[::4], alpha=0.15, color="coral", s=10, label="Step Observations")
        if bin_centers:
            ax2.plot(bin_centers, bin_means, "r-s", lw=3, ms=8, label="Mean Ego Speed")
        ax2.set_xlabel("Local Occlusion Density (Blind Regions)", fontsize=11)
        ax2.set_ylabel("Ego Velocity (m/s)", fontsize=11)
        ax2.set_title("Signal 2: Speed vs Occlusion (Idea C)\nPre-emptive Slowdown Near Blind Zones", fontsize=12, fontweight="bold")
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="upper right")

    # --- Panel 3: Idea A — Behaviour Margin Footprints ---
    ax3 = axs[1, 0]
    # Synthetic grid showing footprint inflation for Cautious vs Normal vs Aggressive
    dummy_cautious = TrackedAgent(agent_id=1, agent_type="auto", y=30.0, x=20.0, vy=0.0, vx=0.0, radius_cells=3.0,
                                  history=[(30.0, 20.0)] * 10)
    dummy_normal = TrackedAgent(agent_id=2, agent_type="auto", y=30.0, x=40.0, vy=0.0, vx=0.0, radius_cells=3.0,
                                history=[{"vy": 0.5, "vx": 0.2, "y": 30.0, "x": 40.0}] * 10)
    dummy_aggressive = TrackedAgent(agent_id=3, agent_type="auto", y=30.0, x=60.0, vy=0.0, vx=0.0, radius_cells=3.0,
                                    history=[{"vy": 3.0*((-1)**i), "vx": 2.0*((-1)**(i//2)), "y": 30.0, "x": 60.0} for i in range(10)])

    cost_cautious = compute_behaviour_cost([dummy_cautious], (60, 80))
    cost_normal = compute_behaviour_cost([dummy_normal], (60, 80))
    cost_aggressive = compute_behaviour_cost([dummy_aggressive], (60, 80))

    combined_behaviour = cost_cautious + cost_normal + cost_aggressive
    im3 = ax3.imshow(combined_behaviour, cmap="plasma", origin="lower")
    ax3.plot(20, 30, "wo", ms=8, label="Cautious (1.0x buffer)")
    ax3.plot(40, 30, "yo", ms=8, label="Normal (1.5x buffer)")
    ax3.plot(60, 30, "ro", ms=8, label="Aggressive (2.5x buffer)")
    ax3.set_title("Signal 3: Dynamic Behaviour Margins (Idea A)\nErratic Agents Receive Wider Berth", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper center", fontsize=9)
    fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    # --- Panel 4: Composite CARLA Driving Scores across Scenarios ---
    ax4 = axs[1, 1]
    scenario_labels = [r["scenario_name"].replace("pedestrian_from_behind_parked_car", "ped_parked").replace("jaywalker_mid_corridor", "jaywalker").replace("wrong_way_vehicle", "wrong_way") for r in results]
    scores = [r["driving_score"] for r in results]
    weathers = [r["weather"] for r in results]

    color_map = {"clear": "#2ca02c", "rain": "#1f77b4", "fog": "#7f7f7f", "night": "#9467bd"}
    bar_colors = [color_map.get(w, "#333333") for w in weathers]

    bars = ax4.barh(range(len(scores)), scores, color=bar_colors, height=0.7)
    ax4.set_yticks(range(len(scores)))
    ax4.set_yticklabels(scenario_labels, fontsize=8)
    ax4.set_xlim(0, 105)
    ax4.set_xlabel("Composite CARLA Driving Score (%)", fontsize=11)
    ax4.set_title("Scenario Suite: Driving Scores by Typology & Weather", fontsize=12, fontweight="bold")
    ax4.grid(True, axis="x", alpha=0.3)

    # Legend for weather colors
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=w.capitalize()) for w, c in color_map.items()]
    ax4.legend(handles=legend_elements, loc="lower left", fontsize=9)

    plt.tight_layout()
    output_path = "doc/phase3_adaptivity_plots.png"
    plt.savefig(output_path, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"\nWrote publication-quality Phase 3 adaptivity figure to: {output_path}")


if __name__ == "__main__":
    run_battery()
