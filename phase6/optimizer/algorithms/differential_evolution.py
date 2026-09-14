"""
Differential Evolution (DE) for shelter-design optimization.

Classic DE/rand/1/bin scheme, adapted for the mixed continuous /
categorical genome used across this project:

    population    -> list of `population_size` genomes
    candidate design -> one genome
    mutation      -> for each numeric gene: donor = x_r1 + F * (x_r2 - x_r3)
                     for each categorical gene: donor = random choice from
                     one of the three sampled parents (DE has no natural
                     notion of "vector difference" for categories)
    crossover     -> binomial crossover: each gene taken from the donor
                     with probability CR, otherwise kept from the target
    selection     -> greedy: trial vector replaces target iff it has
                     equal or better fitness (this is what makes DE a
                     hill-climbing / elitist algorithm by construction)
    iteration     -> one full pass generating a trial for every
                     population member
"""

import random
from optimizer.algorithms.design_space import (
    DEFAULT_DESIGN_SPACE, random_genome, clamp_gene, genome_to_design,
)
from optimizer.objectives.fitness import evaluate_candidate


def run_differential_evolution(
    climate,
    evaluator,
    design_space=None,
    constraints=None,
    weights=None,
    population_size=40,
    generations=30,
    F=0.6,     # differential (mutation) weight
    CR=0.7,    # crossover probability
    seed=42,
    top_n=5,
):
    design_space = design_space or DEFAULT_DESIGN_SPACE
    rng = random.Random(seed)

    population = [random_genome(design_space, rng) for _ in range(population_size)]

    def score_of(genome):
        design = genome_to_design(genome)
        return evaluate_candidate(design, climate, evaluator, constraints, weights)

    fitness_cache = [score_of(g) for g in population]
    history = []
    all_evaluations = [(dict(g), m) for g, m in zip(population, fitness_cache)]

    for gen in range(generations):
        new_population = []
        new_fitness = []

        for i in range(population_size):
            idxs = [j for j in range(population_size) if j != i]
            r1, r2, r3 = rng.sample(idxs, 3)
            target = population[i]
            a, b, c = population[r1], population[r2], population[r3]

            donor = {}
            for gene_name, gene_def in design_space.items():
                if gene_def["type"] == "float":
                    val = a[gene_name] + F * (b[gene_name] - c[gene_name])
                    donor[gene_name] = clamp_gene(gene_name, val, gene_def)
                else:
                    donor[gene_name] = rng.choice([a[gene_name], b[gene_name], c[gene_name]])

            trial = {}
            forced_gene = rng.choice(list(design_space.keys()))
            for gene_name in design_space:
                if gene_name == forced_gene or rng.random() < CR:
                    trial[gene_name] = donor[gene_name]
                else:
                    trial[gene_name] = target[gene_name]

            trial_metrics = score_of(trial)
            all_evaluations.append((dict(trial), trial_metrics))

            if trial_metrics["score"] >= fitness_cache[i]["score"]:
                new_population.append(trial)
                new_fitness.append(trial_metrics)
            else:
                new_population.append(target)
                new_fitness.append(fitness_cache[i])

        population = new_population
        fitness_cache = new_fitness

        best_idx = max(range(population_size), key=lambda k: fitness_cache[k]["score"])
        best_score = fitness_cache[best_idx]["score"]
        avg_score = sum(m["score"] for m in fitness_cache) / population_size

        history.append({
            "generation": gen,
            "best_score": best_score,
            "average_score": avg_score,
            "best_comfort_percentage": fitness_cache[best_idx]["comfort_percentage"],
            "best_heat_loss_kwh": fitness_cache[best_idx]["total_heat_loss_kwh"],
        })

    ranked = sorted(zip(population, fitness_cache), key=lambda item: item[1]["score"], reverse=True)
    top_designs = [
        {"design": genome_to_design(genome), "metrics": metrics}
        for genome, metrics in ranked[:top_n]
    ]
    best_genome, best_metrics = ranked[0]

    return {
        "algorithm": "differential_evolution",
        "best_design": genome_to_design(best_genome),
        "best_metrics": best_metrics,
        "top_designs": top_designs,
        "history": history,
        "all_evaluations": all_evaluations,
    }
