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
import { apiPost, apiGet, delay, USE_MOCK_API } from './client';
import { analysisRuntime } from './analysisApi';

type BackendDesign = {
  id: string;
  length: number;
  width: number;
  height: number;
  wall_thickness: number;
  roof_thickness: number;
  floor_thickness: number;
  insulation_thickness: number;
  opening_percentage: number;
  orientation: string;
  wall_material: string;
  roof_material: string;
  floor_material: string;
  insulation_material: string;
};

type BackendCandidate = {
  design_id: string;
  score: number;
  comfort_percentage: number;
  total_heat_loss: number;
  total_solar_gain: number;
};

function adaptDesign(design: BackendDesign): import('../types').ShelterDesign {
  return {
    id: design.id,
    label: `Backend design ${design.id}`,
    length: design.length,
    width: design.width,
    height: design.height,
    wallThickness: design.wall_thickness,
    roofThickness: design.roof_thickness,
    floorThickness: design.floor_thickness,
    insulationThickness: design.insulation_thickness,
    openingPercentage: design.opening_percentage,
    orientation: design.orientation,
    wallMaterialId: design.wall_material,
    roofMaterialId: design.roof_material,
    floorMaterialId: design.floor_material,
    insulationMaterialId: design.insulation_material,
  };
}

async function resolveRuntime(analysisId: string) {
  const existing = analysisRuntime.get(analysisId) || (analysisId === 'demo' ? [...analysisRuntime.values()][0] : undefined);
  if (existing) return existing;
  const projects = await apiGet<Array<{ id: string; design_ids: string[] }>>('/projects');
  const project = projects[0];
  if (!project?.design_ids?.[0]) throw new Error('No live project is available');
  const runtime = { projectId: project.id, designId: project.design_ids[0], climateId: '' };
  analysisRuntime.set(analysisId, runtime);
  return runtime;
}

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
  if (USE_MOCK_API) {
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

  const runtime = analysisRuntime.get(analysisId);
  if (!runtime) throw new Error('No active runtime found for analysis');

  const created = await apiPost<{ id: string; status: string; progress: number }>('/simulations', {
    project_id: runtime.projectId,
    design_id: runtime.designId,
    climate_id: runtime.climateId,
    duration: 24,
    timestep: 1,
  });
  const started = await apiPost<{ id: string; status: string; progress: number }>(`/simulations/${created.id}/run`, {});
  return adaptSimulation(started, analysisId);
}

// GET /simulations/:id  -> poll for progress (demo: caller advances state)
export async function getSimulationStatus(sim: Simulation): Promise<Simulation> {
  if (!USE_MOCK_API && !sim.isDemo) {
    return adaptSimulation(await apiGet<{ id: string; status: string; progress: number }>(`/simulations/${sim.id}`), sim.analysisId);
  }

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

function adaptSimulation(
  response: { id: string; status: string; progress: number },
  analysisId: string,
): Simulation {
  const status = response.status.toUpperCase();
  const progress = Math.round(response.progress <= 1 ? response.progress * 100 : response.progress);
  const completed = status === 'COMPLETED' || progress >= 100;
  const stageIndex = Math.min(SIMULATION_STAGES.length - 1, Math.floor((progress / 100) * SIMULATION_STAGES.length));
  return {
    id: response.id,
    analysisId,
    status: status === 'FAILED' ? 'Failed' : completed ? 'Completed' : status === 'RUNNING' ? 'Running' : 'Preparing',
    progress,
    currentStage: SIMULATION_STAGES[stageIndex],
    stagesCompleted: SIMULATION_STAGES.slice(0, stageIndex),
    startedAt: new Date().toISOString(),
    isDemo: false,
  };
}

// GET /simulations/:id/results
export async function getSimulationResults(_simulationId: string): Promise<SimulationResult> {
  if (USE_MOCK_API) return delay(SIMULATION_RESULT, 300);
  const res = await apiGet<any>(`/simulations/${_simulationId}/results`);
  return {
    simulationId: res.simulation_id,
    averageIndoorTemp: res.average_temperature,
    minIndoorTemp: res.minimum_temperature,
    maxIndoorTemp: res.maximum_temperature,
    comfortPercentage: res.comfort_percentage,
    heatLoss: res.total_heat_loss,
    solarGain: res.total_solar_gain,
    externalEnergyRequirement: res.total_heat_loss,
    comfortBandMin: SIMULATION_RESULT.comfortBandMin,
    comfortBandMax: SIMULATION_RESULT.comfortBandMax,
    hourly: SIMULATION_RESULT.hourly,
  };
}

// GET /optimization/:analysisId
export async function getOptimizationResults(_analysisId: string): Promise<OptimizationResult> {
  if (USE_MOCK_API) return delay(OPTIMIZATION_RESULT, 300);
  const runtime = await resolveRuntime(_analysisId);
  const created = await apiPost<{ id: string }>('/optimization', {
    project_id: runtime.projectId,
    baseline_design_id: runtime.designId,
    parameters: { max_candidates: 5 },
  });
  const result = await apiPost<{
    candidates: BackendCandidate[];
    best_candidate_design_id?: string;
  }>(`/optimization/${created.id}/run?climate_location=Composite`, {});
  const topDesigns = await Promise.all(result.candidates.map(async (candidate) => {
    const design = await apiGet<BackendDesign>(`/designs/${candidate.design_id}`);
    return {
      designId: candidate.design_id,
      designLabel: `Candidate ${candidate.design_id}`,
      isRecommended: candidate.design_id === result.best_candidate_design_id,
      isBaseline: false,
      comfortPercentage: candidate.comfort_percentage,
      heatLoss: candidate.total_heat_loss,
      solarGain: candidate.total_solar_gain,
      externalEnergyRequirement: candidate.total_heat_loss,
      overallScore: candidate.score,
      design: adaptDesign(design),
    };
  }));
  return {
    algorithm: 'Backend mock optimizer',
    candidatesEvaluated: topDesigns.length,
    generations: 1,
    bestScore: topDesigns[0]?.overallScore || 0,
    bestDesignId: result.best_candidate_design_id || topDesigns[0]?.designId || '',
    convergence: topDesigns.length ? [{ generation: 1, bestScore: topDesigns[0].overallScore, averageScore: topDesigns.reduce((sum, item) => sum + item.overallScore, 0) / topDesigns.length }] : [],
    topDesigns,
    sensitivity: [
      { factor: 'Insulation thickness', importance: 0.35 },
      { factor: 'Opening percentage', importance: 0.25 },
      { factor: 'Material conductivity', importance: 0.2 },
    ],
  };
}

// GET /comparison/:analysisId
export async function getComparison(_analysisId: string): Promise<ScenarioResult[]> {
  if (USE_MOCK_API || _analysisId === 'demo') return delay(SCENARIO_RESULTS, 250);
  const runtime = await resolveRuntime(_analysisId);
  const response = await apiPost<{ best_design_id?: string; metrics: Array<{ design_id: string; comfort_percentage: number; total_heat_loss: number; total_solar_gain: number; energy_requirement: number; overall_score: number }> }>('/comparisons?climate_location=Composite', { design_ids: [runtime.designId] });
  return Promise.all(response.metrics.map(async (metric) => ({
    designId: metric.design_id,
    designLabel: `Design ${metric.design_id}`,
    isRecommended: metric.design_id === response.best_design_id,
    isBaseline: metric.design_id === runtime.designId,
    comfortPercentage: metric.comfort_percentage,
    heatLoss: metric.total_heat_loss,
    solarGain: metric.total_solar_gain,
    externalEnergyRequirement: metric.energy_requirement,
    overallScore: metric.overall_score,
    design: adaptDesign(await apiGet<BackendDesign>(`/designs/${metric.design_id}`)),
  })));
}

// GET /recommendation/:analysisId
export async function getRecommendation(_analysisId: string): Promise<Recommendation> {
  if (USE_MOCK_API) {
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

  const runtime = await resolveRuntime(_analysisId);
  const res = await apiGet<any>(`/projects/${runtime.projectId}/recommendation?climate_location=Composite`);
  const design = await apiGet<BackendDesign>(`/designs/${res.recommended_design_id}`);
  return {
    design: adaptDesign(design),
    result: {
      designId: res.recommended_design_id,
      designLabel: `Design ${res.recommended_design_id}`,
      isRecommended: true,
      isBaseline: false,
      comfortPercentage: res.performance.comfort_percentage || 0,
      heatLoss: res.performance.total_heat_loss || 0,
      solarGain: res.performance.total_solar_gain || 0,
      externalEnergyRequirement: res.performance.energy_requirement || 0,
      overallScore: res.score,
      design: adaptDesign(design),
    },
    performance: {
      comfort: res.performance.comfort_percentage || 0,
      heatLoss: res.performance.total_heat_loss || 0,
      solarGain: res.performance.total_solar_gain || 0,
      externalEnergyRequirement: res.performance.energy_requirement || 0,
    },
    explanation: res.explanation,
    tradeoffs: [],
    assumptions: res.assumptions,
    limitations: res.limitations,
  };
}

export async function getReport(analysisId: string): Promise<Report> {
  if (USE_MOCK_API) {
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

  const runtime = await resolveRuntime(analysisId);
  const res = await apiGet<any>(`/projects/${runtime.projectId}/report?climate_location=Composite`);
  const recommendation = await getRecommendation(analysisId);
  const comparison = await getComparison(analysisId);
  const optimizationResult = await getOptimizationResults(analysisId);
  
  return {
    project: {
      id: analysisId,
      name: res.project.name,
      createdAt: res.project.created_at,
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
    materials: Object.values(res.materials).map((m: any) => ({
      id: m.id,
      name: m.name,
      category: (m.category.charAt(0).toUpperCase() + m.category.slice(1)) as import('../types').MaterialCategory,
      thermalConductivity: m.thermal_conductivity,
      density: m.density,
      specificHeat: m.specific_heat,
      costFactor: m.cost_factor,
      description: 'Material supplied by backend',
    })),
    simulationResult: await getSimulationResults("sim-dummy").catch(() => SIMULATION_RESULT),
    optimizationResult,
    comparison,
    recommendation,
    generatedAt: new Date().toISOString(),
  };
}
