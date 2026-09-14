import { ClimateData, ClimateProfile } from '../types';
import { CLIMATE_PRESETS, LADAKH_PROFILE } from '../mock/climate';
import { delay } from './client';

// GET /climate/presets
export async function getClimatePresets() {
  return delay(CLIMATE_PRESETS);
}

// GET /climate?presetId=
export async function getClimate(presetId: string = 'ladakh'): Promise<ClimateData> {
  const preset = CLIMATE_PRESETS.find((p) => p.id === presetId) ?? CLIMATE_PRESETS[0];
  return delay(preset.climate);
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
