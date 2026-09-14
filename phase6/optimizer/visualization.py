"""
Optional matplotlib visualizations. Kept entirely separate from the
optimization logic — these functions only ever *read* results that
were already computed elsewhere; they never influence the search.

All functions are safe to skip (e.g. in headless/test environments) —
just don't call them. Each saves a PNG to the given path.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_convergence(history_by_algo: dict, save_path="convergence.png"):
    plt.figure(figsize=(8, 5))
    for algo_name, history in history_by_algo.items():
        gens = [h["generation"] for h in history]
        best = [h["best_score"] for h in history]
        avg = [h["average_score"] for h in history]
        plt.plot(gens, best, label=f"{algo_name} best")
        plt.plot(gens, avg, "--", alpha=0.6, label=f"{algo_name} avg")
    plt.xlabel("Generation / Iteration")
    plt.ylabel("Objective score")
    plt.title("Optimization convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot_top_designs(top_designs: list, save_path="top_designs.png"):
    names = [f"#{i+1}" for i in range(len(top_designs))]
    scores = [d["metrics"]["score"] for d in top_designs]
    comforts = [d["metrics"]["comfort_percentage"] for d in top_designs]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(names, scores, color="steelblue", alpha=0.8, label="Score")
    ax1.set_ylabel("Score")
    ax2 = ax1.twinx()
    ax2.plot(names, comforts, color="darkorange", marker="o", label="Comfort %")
    ax2.set_ylabel("Comfort (%)")
    plt.title("Top candidate designs")
    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot_sensitivity(sensitivity_result: dict, save_path="sensitivity.png"):
    ranked = sensitivity_result["ranked_parameters"]
    params = [r["parameter"] for r in ranked]
    impacts = [r["percent_impact"] for r in ranked]

    plt.figure(figsize=(8, 6))
    plt.barh(params[::-1], impacts[::-1], color="mediumseagreen")
    plt.xlabel("Impact on score (%)")
    plt.title("Parameter sensitivity ranking")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot_temperature_profile(metrics: dict, climate_name="", save_path="temperature_profile.png"):
    indoor = metrics["hourly_indoor_temp"]
    outdoor = metrics["hourly_outdoor_temp"]
    hours = list(range(len(indoor)))

    plt.figure(figsize=(8, 5))
    plt.plot(hours, indoor, label="Indoor (passive)", color="crimson")
    plt.plot(hours, outdoor, label="Outdoor", color="steelblue")
    plt.xlabel("Hour of day")
    plt.ylabel("Temperature (°C)")
    plt.title(f"Temperature profile - best design ({climate_name})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot_scenario_comparison(scenario_result: dict, save_path="scenario_comparison.png"):
    names = list(scenario_result["per_scenario"].keys())
    comforts = [scenario_result["per_scenario"][n]["comfort_percentage"] for n in names]
    heat_losses = [scenario_result["per_scenario"][n]["total_heat_loss_kwh"] for n in names]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    x = range(len(names))
    ax1.bar(x, comforts, color="seagreen", alpha=0.8, label="Comfort %")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(names, rotation=20, ha="right")
    ax1.set_ylabel("Comfort (%)")
    ax2 = ax1.twinx()
    ax2.plot(x, heat_losses, color="firebrick", marker="o", label="Heat loss (kWh)")
    ax2.set_ylabel("Heat loss (kWh/day)")
    plt.title("Scenario comparison for recommended design")
    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()
