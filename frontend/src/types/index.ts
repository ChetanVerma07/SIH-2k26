// ==========================================================================
// Centralized type definitions for the Passive Shelter Design Platform
// These types define the contract that will later be served by a
// FastAPI backend. Mock data in src/mock conforms to these shapes.
// ==========================================================================

export type ClimateType =
  | 'High Altitude Cold'
  | 'Hot & Dry'
  | 'Warm & Humid'
  | 'Composite'
  | 'User Defined';

export interface ClimateData {
  locationName: string;
  latitude: number;
  longitude: number;
  climateType: ClimateType;
  ambientTemperature: number; // deg C, current/representative
  relativeHumidity: number; // %
  atmosphericPressure: number; // kPa
  solarRadiation: number; // W/m^2
  windSpeed: number; // m/s
}

export interface ClimateProfilePoint {
  hour: number; // 0-23
  temperature: number; // deg C
  humidity: number; // %
  pressure: number; // kPa
  solarRadiation: number; // W/m^2
  windSpeed: number; // m/s
}

export interface ClimateProfile {
  location: string;
  climateType: ClimateType;
  points: ClimateProfilePoint[];
}

export type MaterialCategory = 'Wall' | 'Roof' | 'Floor' | 'Insulation';

export interface Material {
  id: string;
  name: string;
  category: MaterialCategory;
  thermalConductivity: number; // W/mK
  density: number; // kg/m3
  specificHeat: number; // J/kgK
  costFactor: number; // relative index 1-10
  description: string;
}

export interface ShelterDesign {
  id: string;
  label: string;
  length: number; // m
  width: number; // m
  height: number; // m
  wallThickness: number; // m
  roofThickness: number; // m
  floorThickness: number; // m
  insulationThickness: number; // m
  openingPercentage: number; // % of wall area
  orientation: string; // e.g. 'South', 'North-East'
  wallMaterialId: string;
  roofMaterialId: string;
  floorMaterialId: string;
  insulationMaterialId: string;
}

export interface ShelterRequirements {
  targetIndoorTempMin: number;
  targetIndoorTempMax: number;
  occupants: number;
  floorArea: number;
  budget: number;
  simulationDurationHours: number;
}

export type DesignMode = 'AUTO_OPTIMIZE' | 'MANUAL';

export interface AnalysisProject {
  id: string;
  name: string;
  createdAt: string;
  climate: ClimateData;
  requirements: ShelterRequirements;
  design: ShelterDesign;
  designMode: DesignMode;
  status: 'draft' | 'queued' | 'simulating' | 'completed' | 'failed';
}

export type SimulationStage =
  | 'Climate data'
  | 'Design preparation'
  | 'Thermal simulation'
  | 'Optimization'
  | 'Validation'
  | 'Recommendation';

export type SimulationStatus = 'Preparing' | 'Running' | 'Completed' | 'Failed';

export interface Simulation {
  id: string;
  analysisId: string;
  status: SimulationStatus;
  progress: number; // 0-100
  currentStage: SimulationStage;
  stagesCompleted: SimulationStage[];
  startedAt: string;
  isDemo: boolean;
}

export interface HourlyResultPoint {
  hour: number;
  indoorTemp: number;
  outdoorTemp: number;
  solarRadiation: number;
  heatLoss: number; // W
}

export interface TimeSeriesPoint {
  hour: number
  ambientTempC: number
  indoorTempC: number
  solarGainW: number
  wallLossW: number
  roofLossW: number
  floorLossW: number
  openingLossW: number
  totalLossW: number
}

export interface HeatFlowBreakdown {
  walls: number
  roof: number
  floor: number
  openings: number
}

export interface SimulationResult {
  simulationId: string;
  averageIndoorTemp: number;
  minIndoorTemp: number;
  maxIndoorTemp: number;
  comfortPercentage: number; // % of time within comfort band
  heatLoss: number; // total, kWh
  solarGain: number; // total, kWh
  externalEnergyRequirement: number; // kWh
  comfortBandMin: number;
  comfortBandMax: number;
  hourly: HourlyResultPoint[];
}

export interface ScenarioResult {
  designId: string;
  designLabel: string;
  isRecommended: boolean;
  isBaseline: boolean;
  comfortPercentage: number;
  heatLoss: number;
  solarGain: number;
  externalEnergyRequirement: number;
  overallScore: number; // 0-100
  design: ShelterDesign;
}

export interface OptimizationGenerationPoint {
  generation: number;
  bestScore: number;
  averageScore: number;
}

export interface SensitivityFactor {
  factor: string;
  importance: number; // 0-1
}

export interface OptimizationResult {
  algorithm: string;
  candidatesEvaluated: number;
  generations: number;
  bestScore: number;
  bestDesignId: string;
  convergence: OptimizationGenerationPoint[];
  topDesigns: ScenarioResult[];
  sensitivity: SensitivityFactor[];
}

export interface Recommendation {
  design: ShelterDesign;
  result: ScenarioResult;
  performance: {
    comfort: number;
    heatLoss: number;
    solarGain: number;
    externalEnergyRequirement: number;
  };
  explanation: string;
  tradeoffs: string[];
  assumptions: string[];
  limitations: string[];
}

export interface Report {
  project: AnalysisProject;
  climateProfile: ClimateProfile;
  materials: Material[];
  simulationResult: SimulationResult;
  optimizationResult: OptimizationResult;
  comparison: ScenarioResult[];
  recommendation: Recommendation;
  generatedAt: string;
}
