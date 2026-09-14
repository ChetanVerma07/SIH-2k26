import { ClimateData, ClimateProfile } from '../types';
import { CLIMATE_PRESETS, LADAKH_PROFILE } from '../mock/climate';
import { apiGet, delay, USE_MOCK_API } from './client';

type BackendClimate = {
  id: string;
  location?: string;
  temperature: number;
  humidity: number;
  pressure: number;
  solar_radiation: number;
  wind_speed: number;
};

const LOCATION_BY_PRESET: Record<string, string> = {
  ladakh: 'Ladakh',
  'hot-dry': 'Hot and Dry',
  'warm-humid': 'Warm and Humid',
  composite: 'Composite',
};

function adaptClimate(climate: BackendClimate): ClimateData {
  const location = climate.location || 'Unknown location';
  const preset = CLIMATE_PRESETS.find((item) => item.name.toLowerCase().includes(location.toLowerCase()));
  return {
    locationName: location,
    latitude: preset?.climate.latitude ?? 0,
    longitude: preset?.climate.longitude ?? 0,
    climateType: preset?.climateType ?? 'User Defined',
    ambientTemperature: climate.temperature,
    relativeHumidity: climate.humidity,
    atmosphericPressure: climate.pressure / 10,
    solarRadiation: climate.solar_radiation,
    windSpeed: climate.wind_speed / 3.6,
  };
}

// GET /climate/presets
export async function getClimatePresets() {
  if (USE_MOCK_API) return delay(CLIMATE_PRESETS);

  const response = await apiGet<BackendClimate[]>('/climate/presets');
  return response.map((climate) => {
    const adapted = adaptClimate(climate);
    const source = CLIMATE_PRESETS.find((item) => item.name.toLowerCase().includes((climate.location || '').toLowerCase()));
    return {
      id: Object.entries(LOCATION_BY_PRESET).find(([, location]) => location === climate.location)?.[0] || climate.id,
      name: source?.name || climate.location || 'Backend climate',
      climateType: adapted.climateType,
      climate: adapted,
    };
  });
}

// GET /climate?presetId=
export async function getClimate(presetId: string = 'ladakh'): Promise<ClimateData> {
  const preset = CLIMATE_PRESETS.find((p) => p.id === presetId) ?? CLIMATE_PRESETS[0];
  if (USE_MOCK_API) return delay(preset.climate);

  return adaptClimate(await apiGet<BackendClimate>(`/climate/current/${encodeURIComponent(LOCATION_BY_PRESET[presetId] || preset.climate.locationName)}`));
}

// GET /climate/profile?presetId=
export async function getClimateProfile(presetId: string = 'ladakh'): Promise<ClimateProfile> {
  // Only the Ladakh scenario has a full deterministic 24h dataset in this
  // demo phase; other presets reuse its shape scaled by ambient temperature.
  if (presetId === 'ladakh') return delay(LADAKH_PROFILE);
  const preset = CLIMATE_PRESETS.find((p) => p.id === presetId) ?? CLIMATE_PRESETS[0];
  const offset = preset.climate.ambientTemperature - LADAKH_PROFILE.points[12].temperature;
  const scaled: ClimateProfile = {
    location: preset.climate.locationName,
    climateType: preset.climateType,
    points: LADAKH_PROFILE.points.map((p) => ({
      ...p,
      temperature: Number((p.temperature + offset).toFixed(1)),
    })),
  };
  return delay(scaled);
}
