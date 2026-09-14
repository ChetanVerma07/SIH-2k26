import { OptimizationResult, OptimizationGenerationPoint, SensitivityFactor } from '../types';
import { SCENARIO_RESULTS, RECOMMENDED_DESIGN } from './designs';

const convergence: OptimizationGenerationPoint[] = [
  { generation: 1, bestScore: 52, averageScore: 40 },
  { generation: 2, bestScore: 58, averageScore: 44 },
  { generation: 3, bestScore: 64, averageScore: 49 },
  { generation: 4, bestScore: 69, averageScore: 53 },
  { generation: 5, bestScore: 74, averageScore: 58 },
  { generation: 6, bestScore: 79, averageScore: 62 },
  { generation: 7, bestScore: 83, averageScore: 66 },
  { generation: 8, bestScore: 86, averageScore: 70 },
  { generation: 9, bestScore: 89, averageScore: 73 },
  { generation: 10, bestScore: 91, averageScore: 76 },
];

const sensitivity: SensitivityFactor[] = [
  { factor: 'Insulation Thickness', importance: 0.34 },
  { factor: 'Wall Material', importance: 0.24 },
  { factor: 'Opening Percentage', importance: 0.18 },
  { factor: 'Orientation', importance: 0.14 },
  { factor: 'Shelter Size', importance: 0.1 },
];

export const OPTIMIZATION_RESULT: OptimizationResult = {
  algorithm: 'NSGA-II (Genetic Multi-Objective)',
  candidatesEvaluated: 480,
  generations: 10,
  bestScore: 91,
  bestDesignId: RECOMMENDED_DESIGN.id,
  convergence,
  topDesigns: [...SCENARIO_RESULTS].sort((a, b) => b.overallScore - a.overallScore).slice(0, 5),
  sensitivity,
};
