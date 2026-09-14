"""
Genetic Algorithm for shelter-design optimization.

Terminology (as required by the spec):
    population    -> a list of `population_size` genomes (candidate designs)
    candidate design -> one genome (flat dict of gene_name -> value)
    fitness/objective -> score returned by objectives.fitness.evaluate_candidate
    selection     -> tournament selection biased towards higher fitness
    crossover     -> uniform crossover: each gene independently taken from
                     parent A or parent B
    mutation      -> gaussian perturbation for numeric genes, random reset
                     for categorical genes (see design_space.mutate_gene)
    generation    -> one full population replacement cycle

Elitism keeps the best `elite_count` genomes unchanged each generation
so fitness can never regress.
"""

import random
from optimizer.algorithms.design_space import (
    DEFAULT_DESIGN_SPACE, random_genome, mutate_gene, clamp_gene, genome_to_design,
)
from optimizer.objectives.fitness import evaluate_candidate


def _tournament_select(scored_population, rng, k=3):
    contenders = rng.sample(scored_population, k)
    return max(contenders, key=lambda item: item[1]["score"])[0]


def _crossover(parent_a, parent_b, rng):
    child = {}
    for gene in parent_a:
        child[gene] = parent_a[gene] if rng.random() < 0.5 else parent_b[gene]
    return child


def run_genetic_algorithm(
    climate,
    evaluator,
    design_space=None,
    constraints=None,
    weights=None,
    population_size=40,
    generations=30,
    elite_count=3,
    mutation_rate=0.25,
    mutation_strength=0.15,
    seed=42,
    top_n=5,
):
    design_space = design_space or DEFAULT_DESIGN_SPACE
    rng = random.Random(seed)

    population = [random_genome(design_space, rng) for _ in range(population_size)]
    history = []
    all_evaluations = []  # (genome, metrics) collected for optional surrogate training

    scored = None
    for gen in range(generations):
        scored = []
        for genome in population:
            design = genome_to_design(genome)
            metrics = evaluate_candidate(design, climate, evaluator, constraints, weights)
            scored.append((genome, metrics))
            all_evaluations.append((dict(genome), metrics))

        scored.sort(key=lambda item: item[1]["score"], reverse=True)
        best_score = scored[0][1]["score"]
        avg_score = sum(m["score"] for _, m in scored) / len(scored)
        best_comfort = scored[0][1]["comfort_percentage"]
        best_heat_loss = scored[0][1]["total_heat_loss_kwh"]

        history.append({
            "generation": gen,
            "best_score": best_score,
            "average_score": avg_score,
            "best_comfort_percentage": best_comfort,
            "best_heat_loss_kwh": best_heat_loss,
        })

        next_population = [genome for genome, _ in scored[:elite_count]]
        while len(next_population) < population_size:
            parent_a = _tournament_select(scored, rng)
            parent_b = _tournament_select(scored, rng)
            child = _crossover(parent_a, parent_b, rng)
            for gene_name, gene_def in design_space.items():
                if rng.random() < mutation_rate:
                    child[gene_name] = mutate_gene(gene_name, child[gene_name], gene_def, rng,
                                                    mutation_strength)
                else:
                    child[gene_name] = clamp_gene(gene_name, child[gene_name], gene_def)
            next_population.append(child)

        population = next_population

    scored.sort(key=lambda item: item[1]["score"], reverse=True)
    top_designs = [
        {"design": genome_to_design(genome), "metrics": metrics}
        for genome, metrics in scored[:top_n]
    ]

    best_genome, best_metrics = scored[0]
    return {
        "algorithm": "genetic_algorithm",
        "best_design": genome_to_design(best_genome),
        "best_metrics": best_metrics,
        "top_designs": top_designs,
        "history": history,
        "all_evaluations": all_evaluations,
    }
