import { ShelterDesign, ScenarioResult, SimulationResult, HourlyResultPoint } from '../types';
import { LADAKH_PROFILE } from './climate';

export const BASELINE_DESIGN: ShelterDesign = {
  id: 'design-baseline',
  label: 'Compact Passive Shelter',
  length: 6,
  width: 4,
  height: 2.8,
  wallThickness: 0.3,
  roofThickness: 0.15,
  floorThickness: 0.1,
  insulationThickness: 0.03,
  openingPercentage: 18,
  orientation: 'North',
  wallMaterialId: 'wall-fired-brick',
  roofMaterialId: 'roof-metal-sheet',
  floorMaterialId: 'floor-stone-tile',
  insulationMaterialId: 'insulation-eps',
};

export const DESIGN_A: ShelterDesign = {
  id: 'design-a',
  label: 'High-Insulation Shelter',
  length: 6,
  width: 4,
  height: 2.7,
  wallThickness: 0.4,
  roofThickness: 0.2,
  floorThickness: 0.12,
  insulationThickness: 0.08,
  openingPercentage: 12,
  orientation: 'South',
  wallMaterialId: 'wall-rammed-earth',
  roofMaterialId: 'roof-timber-earth',
  floorMaterialId: 'floor-compacted-earth',
  insulationMaterialId: 'insulation-mineral-wool',
};

export const DESIGN_B: ShelterDesign = {
  id: 'design-b',
  label: 'Thermal-Mass Shelter',
  length: 5.5,
  width: 4.2,
  height: 2.6,
  wallThickness: 0.45,
  roofThickness: 0.22,
  floorThickness: 0.12,
  insulationThickness: 0.1,
  openingPercentage: 9,
  orientation: 'South-East',
  wallMaterialId: 'wall-stone-masonry',
  roofMaterialId: 'roof-timber-earth',
  floorMaterialId: 'floor-compacted-earth',
  insulationMaterialId: 'insulation-strawbale',
};

export const SOLAR_OPTIMIZED_DESIGN: ShelterDesign = {
  id: 'design-solar-optimized', label: 'Solar-Optimized Shelter', length: 6.2, width: 3.8, height: 2.7,
  wallThickness: 0.32, roofThickness: 0.16, floorThickness: 0.1, insulationThickness: 0.08,
  openingPercentage: 16, orientation: 'South', wallMaterialId: 'wall-fired-brick', roofMaterialId: 'roof-metal-sheet',
  floorMaterialId: 'floor-stone-tile', insulationMaterialId: 'insulation-mineral-wool',
};

export const THERMAL_MASS_DESIGN: ShelterDesign = {
  id: 'design-thermal-mass-plus', label: 'Thermal-Mass Shelter Plus', length: 5.6, width: 4.4, height: 2.5,
  wallThickness: 0.5, roofThickness: 0.2, floorThickness: 0.14, insulationThickness: 0.07,
  openingPercentage: 8, orientation: 'South-East', wallMaterialId: 'wall-stone-masonry', roofMaterialId: 'roof-timber-earth',
  floorMaterialId: 'floor-compacted-earth', insulationMaterialId: 'insulation-strawbale',
};

export const HYBRID_PASSIVE_DESIGN: ShelterDesign = {
  id: 'design-hybrid-passive', label: 'Hybrid Passive Shelter', length: 5.9, width: 4, height: 2.65,
  wallThickness: 0.38, roofThickness: 0.18, floorThickness: 0.12, insulationThickness: 0.1,
  openingPercentage: 11, orientation: 'South', wallMaterialId: 'wall-rammed-earth', roofMaterialId: 'roof-timber-earth',
  floorMaterialId: 'floor-compacted-earth', insulationMaterialId: 'insulation-mineral-wool',
};

export const RECOMMENDED_DESIGN: ShelterDesign = {
  id: 'design-recommended',
  label: 'Recommended Design',
  length: 5.8,
  width: 4.1,
  height: 2.6,
  wallThickness: 0.42,
  roofThickness: 0.2,
  floorThickness: 0.12,
  insulationThickness: 0.12,
  openingPercentage: 10,
  orientation: 'South',
  wallMaterialId: 'wall-rammed-earth',
  roofMaterialId: 'roof-timber-earth',
  floorMaterialId: 'floor-compacted-earth',
  insulationMaterialId: 'insulation-yak-wool',
};

export const ALL_DESIGNS: ShelterDesign[] = [
  BASELINE_DESIGN,
  DESIGN_A,
  DESIGN_B,
  RECOMMENDED_DESIGN,
  SOLAR_OPTIMIZED_DESIGN,
  THERMAL_MASS_DESIGN,
  HYBRID_PASSIVE_DESIGN,
];

// Deterministic hourly simulation output derived from the Ladakh outdoor
// profile. This models a well-insulated recommended shelter that damps
// outdoor swings and stays closer to the comfort band.
const comfortBandMin = 16;
const comfortBandMax = 22;

const hourly: HourlyResultPoint[] = LADAKH_PROFILE.points.map((p, i) => {
  const indoor = 18.5 + Math.sin((i / 24) * Math.PI * 2 - 1.2) * 2.4;
  const heatLoss = Math.max(200, 900 - p.solarRadiation * 0.6 + Math.abs(indoor - p.temperature) * 15);
  return {
    hour: p.hour,
    indoorTemp: Number(indoor.toFixed(1)),
    outdoorTemp: p.temperature,
    solarRadiation: p.solarRadiation,
    heatLoss: Math.round(heatLoss),
  };
});

const withinComfort = hourly.filter(
  (h) => h.indoorTemp >= comfortBandMin && h.indoorTemp <= comfortBandMax
).length;

export const SIMULATION_RESULT: SimulationResult = {
  simulationId: 'sim-ladakh-recommended',
  averageIndoorTemp: Number(
    (hourly.reduce((s, h) => s + h.indoorTemp, 0) / hourly.length).toFixed(1)
  ),
  minIndoorTemp: Math.min(...hourly.map((h) => h.indoorTemp)),
  maxIndoorTemp: Math.max(...hourly.map((h) => h.indoorTemp)),
  comfortPercentage: Math.round((withinComfort / hourly.length) * 100),
  heatLoss: Number((hourly.reduce((s, h) => s + h.heatLoss, 0) / 1000).toFixed(1)),
  solarGain: Number((hourly.reduce((s, h) => s + h.solarRadiation, 0) * 0.004).toFixed(1)),
  externalEnergyRequirement: 4.2,
  comfortBandMin,
  comfortBandMax,
  hourly,
};

export const SCENARIO_RESULTS: ScenarioResult[] = [
  {
    designId: BASELINE_DESIGN.id,
    designLabel: BASELINE_DESIGN.label,
    isRecommended: false,
    isBaseline: true,
    comfortPercentage: 41,
    heatLoss: 18.6,
    solarGain: 6.1,
    externalEnergyRequirement: 12.4,
    overallScore: 48,
    design: BASELINE_DESIGN,
  },
  {
    designId: DESIGN_A.id,
    designLabel: DESIGN_A.label,
    isRecommended: false,
    isBaseline: false,
    comfortPercentage: 68,
    heatLoss: 11.2,
    solarGain: 7.4,
    externalEnergyRequirement: 7.1,
    overallScore: 71,
    design: DESIGN_A,
  },
  {
    designId: DESIGN_B.id,
    designLabel: DESIGN_B.label,
    isRecommended: false,
    isBaseline: false,
    comfortPercentage: 74,
    heatLoss: 9.4,
    solarGain: 7.0,
    externalEnergyRequirement: 5.9,
    overallScore: 78,
    design: DESIGN_B,
  },
  {
    designId: RECOMMENDED_DESIGN.id,
    designLabel: RECOMMENDED_DESIGN.label,
    isRecommended: true,
    isBaseline: false,
    comfortPercentage: 87,
    heatLoss: 7.2,
    solarGain: 7.6,
    externalEnergyRequirement: 4.2,
    overallScore: 91,
    design: RECOMMENDED_DESIGN,
  },
  ...[
    [SOLAR_OPTIMIZED_DESIGN, 82, 8.8, 7.9, 5.1, 84],
    [THERMAL_MASS_DESIGN, 79, 8.1, 6.8, 5.5, 80],
    [HYBRID_PASSIVE_DESIGN, 84, 7.8, 7.5, 4.8, 86],
  ].map(([design, comfortPercentage, heatLoss, solarGain, externalEnergyRequirement, overallScore]) => ({
    designId: (design as ShelterDesign).id,
    designLabel: (design as ShelterDesign).label,
    isRecommended: false,
    isBaseline: false,
    comfortPercentage: comfortPercentage as number,
    heatLoss: heatLoss as number,
    solarGain: solarGain as number,
    externalEnergyRequirement: externalEnergyRequirement as number,
    overallScore: overallScore as number,
    design: design as ShelterDesign,
  })),
];
