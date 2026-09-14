export interface TerrainSite {
  id: string;
  name: string;
  lat: number;
  lng: number;
  elevation: number;
  solarExposure: 'High' | 'Moderate' | 'Low';
  windExposure: 'High' | 'Moderate' | 'Low';
  terrainSuitability: 'Excellent' | 'Good' | 'Poor';
  thermalPotential: 'High' | 'Moderate' | 'Low';
  suitabilityScore: number;
  isRecommended: boolean;
  recommendedOrientation: string;
  description: string;
}

export const LADAKH_CENTER = {
  lat: 34.1526,
  lng: 77.5771,
  zoom: 12,
  pitch: 60,
  bearing: 45
};

export const MOCK_TERRAIN_SITES: TerrainSite[] = [
  {
    id: 'site-a',
    name: 'Candidate A (Valley Base)',
    lat: 34.1480,
    lng: 77.5700,
    elevation: 3450,
    solarExposure: 'Moderate',
    windExposure: 'Low',
    terrainSuitability: 'Good',
    thermalPotential: 'Moderate',
    suitabilityScore: 78,
    isRecommended: false,
    recommendedOrientation: 'South',
    description: 'A flat area at the base of the valley. Protected from wind but receives less direct solar radiation during winter months.'
  },
  {
    id: 'site-b',
    name: 'Candidate B (Exposed Ridge)',
    lat: 34.1600,
    lng: 77.5850,
    elevation: 3620,
    solarExposure: 'High',
    windExposure: 'High',
    terrainSuitability: 'Poor',
    thermalPotential: 'Low',
    suitabilityScore: 54,
    isRecommended: false,
    recommendedOrientation: 'South-East',
    description: 'High solar exposure but extremely vulnerable to harsh winter winds, increasing the overall thermal load.'
  },
  {
    id: 'site-recommended',
    name: 'AI Recommended Site',
    lat: 34.1540,
    lng: 77.5800,
    elevation: 3520,
    solarExposure: 'High',
    windExposure: 'Moderate',
    terrainSuitability: 'Excellent',
    thermalPotential: 'High',
    suitabilityScore: 92,
    isRecommended: true,
    recommendedOrientation: 'South',
    description: 'Optimal balance of high solar gain and natural terrain shielding from prevailing winds. Gentle slope ideal for foundation.'
  }
];

export const MOCK_THERMAL_ZONES = {
  cold: [77.55, 34.13, 77.60, 34.13, 77.60, 34.17, 77.55, 34.17],
  moderate: [77.56, 34.14, 77.59, 34.14, 77.59, 34.16, 77.56, 34.16],
  warm: [77.575, 34.15, 77.585, 34.15, 77.585, 34.158, 77.575, 34.158],
};

export const MOCK_LADAKH_BOUNDARY = [
  77.55, 34.13, 77.60, 34.13, 77.60, 34.17, 77.55, 34.17, 77.55, 34.13,
];
