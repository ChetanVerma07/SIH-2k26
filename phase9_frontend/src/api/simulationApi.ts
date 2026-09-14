import {
  Simulation,
  SimulationResult,
  SimulationStage,
  OptimizationResult,
  ScenarioResult,
  Recommendation,
  Report,
} from '../types';
import { SIMULATION_RESULT, SCENARIO_RESULTS, RECOMMENDED_DESIGN } from '../mock/designs';
import { OPTIMIZATION_RESULT } from '../mock/optimization';
import { LADAKH_CLIMATE, LADAKH_PROFILE } from '../mock/climate';
import { MATERIALS } from '../mock/materials';
import { delay } from './client';

export const SIMULATION_STAGES: SimulationStage[] = [
  'Climate data',
  'Design preparation',
  'Thermal simulation',
  'Optimization',
  'Validation',
  'Recommendation',
];

// POST /simulations  -> starts a simulation for an analysis
export async function runSimulation(analysisId: string): Promise<Simulation> {
  const sim: Simulation = {
    id: `sim-${Date.now()}`,
    analysisId,
    status: 'Preparing',
    progress: 0,
    currentStage: SIMULATION_STAGES[0],
    stagesCompleted: [],
    startedAt: new Date().toISOString(),
    isDemo: true,
  };
  return delay(sim, 200);
}

// GET /simulations/:id  -> poll for progress (demo: caller advances state)
export async function getSimulationStatus(sim: Simulation): Promise<Simulation> {
  const stageIndex = SIMULATION_STAGES.indexOf(sim.currentStage);
  const nextProgress = Math.min(100, sim.progress + 17);
  const completed = nextProgress >= 100;
  const nextStageIndex = Math.min(
    SIMULATION_STAGES.length - 1,
    Math.floor((nextProgress / 100) * SIMULATION_STAGES.length)
  );
  const updated: Simulation = {
    ...sim,
    progress: nextProgress,
    status: completed ? 'Completed' : 'Running',
    currentStage: SIMULATION_STAGES[nextStageIndex],
    stagesCompleted: SIMULATION_STAGES.slice(0, nextStageIndex),
  };
  return delay(updated, 500);
}

// GET /simulations/:id/results
export async function getSimulationResults(_simulationId: string): Promise<SimulationResult> {
  return delay(SIMULATION_RESULT, 300);
}

// GET /optimization/:analysisId
export async function getOptimizationResults(_analysisId: string): Promise<OptimizationResult> {
  return delay(OPTIMIZATION_RESULT, 300);
}

// GET /comparison/:analysisId
export async function getComparison(_analysisId: string): Promise<ScenarioResult[]> {
  return delay(SCENARIO_RESULTS, 250);
}

// GET /recommendation/:analysisId
export async function getRecommendation(_analysisId: string): Promise<Recommendation> {
  const recommended = SCENARIO_RESULTS.find((s) => s.isRecommended)!;
  const baseline = SCENARIO_RESULTS.find((s) => s.isBaseline)!;
  const rec: Recommendation = {
    design: RECOMMENDED_DESIGN,
    result: recommended,
    performance: {
      comfort: recommended.comfortPercentage,
      heatLoss: recommended.heatLoss,
      solarGain: recommended.solarGain,
      externalEnergyRequirement: recommended.externalEnergyRequirement,
    },
    explanation: `The recommended design achieves ${recommended.comfortPercentage}% thermal comfort, the highest among all evaluated candidates, while cutting heat loss from ${baseline.heatLoss} kWh to ${recommended.heatLoss} kWh compared with the baseline. Increased insulation thickness (0.12 m) combined with a south-facing orientation and reduced opening percentage (10%) lowers external energy requirement to ${recommended.externalEnergyRequirement} kWh, a reduction of ${Math.round(((baseline.externalEnergyRequirement - recommended.externalEnergyRequirement) / baseline.externalEnergyRequirement) * 100)}% relative to the baseline design.`,
    tradeoffs: [
      'Higher wall and insulation thickness increases material cost relative to the baseline.',
      'Reduced opening percentage lowers daylighting compared with the baseline design.',
      'South orientation constrains site layout flexibility on some plots.',
    ],
    assumptions: [
      'Steady periodic thermal behaviour assumed over a representative 24-hour cycle.',
      'Occupant internal heat gains estimated at a fixed average value.',
      'Material properties taken from the standard material library, not site-tested samples.',
    ],
    limitations: [
      'Simulation does not model transient weather events (storms, snow load).',
      'This phase uses mock analytical results, not a coupled ANSYS/CFD simulation.',
      'Structural and seismic performance are outside the scope of this thermal analysis.',
    ],
  };
  return delay(rec, 300);
}

// GET /reports/:analysisId
export async function getReport(analysisId: string): Promise<Report> {
  const recommendation = await getRecommendation(analysisId);
  const comparison = await getComparison(analysisId);
  const optimizationResult = await getOptimizationResults(analysisId);
  const report: Report = {
    project: {
      id: analysisId,
      name: 'Leh Winter Shelter v3',
      createdAt: new Date().toISOString(),
      climate: LADAKH_CLIMATE,
      requirements: {
        targetIndoorTempMin: 16,
        targetIndoorTempMax: 22,
        occupants: 4,
        floorArea: 24,
        budget: 450000,
        simulationDurationHours: 24,
      },
      design: RECOMMENDED_DESIGN,
      designMode: 'AUTO_OPTIMIZE',
      status: 'completed',
    },
    climateProfile: LADAKH_PROFILE,
    materials: MATERIALS,
    simulationResult: SIMULATION_RESULT,
    optimizationResult,
    comparison,
    recommendation,
    generatedAt: new Date().toISOString(),
  };
  return delay(report, 300);
}
