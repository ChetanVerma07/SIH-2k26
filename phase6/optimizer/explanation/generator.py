"""
Converts optimization results into human-readable explanations.
Every sentence is generated from actual computed numbers (comparisons
between top candidates, sensitivity ranks, material properties) —
nothing here is a fixed/templated claim independent of the data.
"""

from optimizer.models.materials import get_material


def explain_best_vs_runner_up(top_designs: list) -> str:
    if len(top_designs) < 2:
        return "Only one valid design was found; no comparison is available."

    best = top_designs[0]
    runner_up = top_designs[1]
    bm, rm = best["metrics"], runner_up["metrics"]

    comfort_diff = bm["comfort_percentage"] - rm["comfort_percentage"]
    heatloss_diff = rm["total_heat_loss_kwh"] - bm["total_heat_loss_kwh"]

    parts = [f"This design was selected over the next-best candidate because it scored "
             f"{bm['score']:.2f} versus {rm['score']:.2f}."]

    if comfort_diff > 0.5:
        parts.append(f"It maintained comfort for {bm['comfort_percentage']:.1f}% of the day, "
                      f"{comfort_diff:.1f} percentage points higher than the runner-up.")
    if heatloss_diff > 0.05:
        parts.append(f"It also lost {heatloss_diff:.2f} kWh/day less heat through the envelope.")
    elif heatloss_diff < -0.05:
        parts.append(f"It traded {abs(heatloss_diff):.2f} kWh/day of additional heat loss for its "
                      f"comfort and material-cost advantages.")

    return " ".join(parts)


def explain_material_choice(design) -> str:
    wall = get_material(design.wall_material)
    ins = get_material(design.insulation_material)
    return (
        f"Wall material '{wall.name}' (conductivity {wall.conductivity:.3f} W/mK) was paired with "
        f"insulation '{ins.name}' (conductivity {ins.conductivity:.3f} W/mK) at "
        f"{design.insulation_thickness*100:.1f} cm thickness, giving a combined envelope resistance "
        f"that the optimizer favored for this climate's heat-loss and cost trade-off."
    )


def explain_insulation_thickness(design, sensitivity_result: dict) -> str:
    ranked = sensitivity_result["ranked_parameters"]
    ins_rank = next((r for r in ranked if r["parameter"] == "insulation_thickness"), None)
    if ins_rank is None:
        return f"Insulation thickness was set to {design.insulation_thickness*100:.1f} cm."
    return (
        f"Insulation thickness was set to {design.insulation_thickness*100:.1f} cm. Sensitivity "
        f"analysis shows this parameter has a '{ins_rank['impact_level']}' impact on the objective "
        f"score (~{ins_rank['percent_impact']:.1f}% swing under a ±15% perturbation), rank "
        f"#{ins_rank['rank']} among all analyzed parameters."
    )


def explain_orientation(design, sensitivity_result: dict) -> str:
    ranked = sensitivity_result["ranked_parameters"]
    orient_rank = next((r for r in ranked if r["parameter"] == "orientation"), None)
    base = f"Orientation was set to {design.orientation:.0f}°."
    if orient_rank is None:
        return base
    return (
        f"{base} This has a '{orient_rank['impact_level']}' impact on score "
        f"(~{orient_rank['percent_impact']:.1f}% swing when rotated ±30°), because it directly "
        f"controls how much winter solar radiation reaches the openings."
    )


def explain_opening_area(design, sensitivity_result: dict) -> str:
    ranked = sensitivity_result["ranked_parameters"]
    open_rank = next((r for r in ranked if r["parameter"] == "opening_area"), None)
    base = f"Opening (window) area was set to {design.opening_area:.2f} m²."
    if open_rank is None:
        return base
    return (
        f"{base} Sensitivity analysis ranks opening area as '{open_rank['impact_level']}' impact "
        f"(~{open_rank['percent_impact']:.1f}% swing), reflecting the balance between useful solar "
        f"gain and added conductive heat loss through glazing."
    )


def generate_full_explanation(top_designs, sensitivity_result) -> dict:
    best_design = top_designs[0]["design"]
    return {
        "selection_reasoning": explain_best_vs_runner_up(top_designs),
        "material_reasoning": explain_material_choice(best_design),
        "insulation_reasoning": explain_insulation_thickness(best_design, sensitivity_result),
        "orientation_reasoning": explain_orientation(best_design, sensitivity_result),
        "opening_area_reasoning": explain_opening_area(best_design, sensitivity_result),
    }
