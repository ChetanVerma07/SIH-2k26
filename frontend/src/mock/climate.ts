import { ClimateData, ClimateProfile, ClimateProfilePoint, ClimateType } from '../types';

// Deterministic 24-hour profile for a Ladakh (High Altitude Cold) winter day.
// Values are illustrative demo data, not measured field data.
const ladakhHourly: ClimateProfilePoint[] = [
  { hour: 0, temperature: -12.5, humidity: 32, pressure: 65.1, solarRadiation: 0, windSpeed: 2.1 },
  { hour: 1, temperature: -13.2, humidity: 33, pressure: 65.1, solarRadiation: 0, windSpeed: 1.9 },
  { hour: 2, temperature: -13.8, humidity: 34, pressure: 65.0, solarRadiation: 0, windSpeed: 1.8 },
  { hour: 3, temperature: -14.3, humidity: 35, pressure: 65.0, solarRadiation: 0, windSpeed: 1.7 },
  { hour: 4, temperature: -14.6, humidity: 35, pressure: 65.0, solarRadiation: 0, windSpeed: 1.6 },
  { hour: 5, temperature: -14.9, humidity: 36, pressure: 65.0, solarRadiation: 0, windSpeed: 1.6 },
  { hour: 6, temperature: -14.1, humidity: 34, pressure: 65.1, solarRadiation: 40, windSpeed: 1.8 },
  { hour: 7, temperature: -11.7, humidity: 31, pressure: 65.1, solarRadiation: 210, windSpeed: 2.2 },
  { hour: 8, temperature: -7.4, humidity: 27, pressure: 65.2, solarRadiation: 430, windSpeed: 2.6 },
  { hour: 9, temperature: -2.8, humidity: 24, pressure: 65.2, solarRadiation: 610, windSpeed: 3.0 },
  { hour: 10, temperature: 1.6, humidity: 21, pressure: 65.3, solarRadiation: 760, windSpeed: 3.3 },
  { hour: 11, temperature: 4.9, humidity: 19, pressure: 65.3, solarRadiation: 860, windSpeed: 3.5 },
  { hour: 12, temperature: 6.8, humidity: 18, pressure: 65.3, solarRadiation: 900, windSpeed: 3.6 },
  { hour: 13, temperature: 7.4, humidity: 18, pressure: 65.3, solarRadiation: 875, windSpeed: 3.7 },
  { hour: 14, temperature: 6.5, humidity: 19, pressure: 65.2, solarRadiation: 780, windSpeed: 3.6 },
  { hour: 15, temperature: 4.1, humidity: 21, pressure: 65.2, solarRadiation: 620, windSpeed: 3.3 },
  { hour: 16, temperature: 0.3, humidity: 24, pressure: 65.2, solarRadiation: 400, windSpeed: 2.9 },
  { hour: 17, temperature: -3.9, humidity: 27, pressure: 65.1, solarRadiation: 180, windSpeed: 2.5 },
  { hour: 18, temperature: -7.2, humidity: 29, pressure: 65.1, solarRadiation: 30, windSpeed: 2.2 },
  { hour: 19, temperature: -9.1, humidity: 30, pressure: 65.1, solarRadiation: 0, windSpeed: 2.0 },
  { hour: 20, temperature: -10.3, humidity: 31, pressure: 65.1, solarRadiation: 0, windSpeed: 1.9 },
  { hour: 21, temperature: -11.2, humidity: 31, pressure: 65.1, solarRadiation: 0, windSpeed: 1.9 },
  { hour: 22, temperature: -11.8, humidity: 32, pressure: 65.1, solarRadiation: 0, windSpeed: 1.8 },
  { hour: 23, temperature: -12.2, humidity: 32, pressure: 65.1, solarRadiation: 0, windSpeed: 1.8 },
];

export const LADAKH_CLIMATE: ClimateData = {
  locationName: 'Leh, Ladakh',
  latitude: 34.1526,
  longitude: 77.5771,
  climateType: 'High Altitude Cold',
  ambientTemperature: -8.4,
  relativeHumidity: 28,
  atmosphericPressure: 65.2,
  solarRadiation: 900,
  windSpeed: 2.8,
};

export const LADAKH_PROFILE: ClimateProfile = {
  location: 'Leh, Ladakh',
  climateType: 'High Altitude Cold',
  points: ladakhHourly,
};

export interface ClimatePreset {
  id: string;
  name: string;
  climateType: ClimateType;
  climate: ClimateData;
}

export const CLIMATE_PRESETS: ClimatePreset[] = [
  {
    id: 'ladakh',
    name: 'Ladakh / High Altitude Cold',
    climateType: 'High Altitude Cold',
    climate: LADAKH_CLIMATE,
  },
  {
    id: 'hot-dry',
    name: 'Hot & Dry (e.g. Jaisalmer)',
    climateType: 'Hot & Dry',
    climate: {
      locationName: 'Jaisalmer, Rajasthan',
      latitude: 26.9157,
      longitude: 70.9083,
      climateType: 'Hot & Dry',
      ambientTemperature: 38.5,
      relativeHumidity: 18,
      atmosphericPressure: 100.9,
      solarRadiation: 950,
      windSpeed: 3.4,
    },
  },
  {
    id: 'warm-humid',
    name: 'Warm & Humid (e.g. Kochi)',
    climateType: 'Warm & Humid',
    climate: {
      locationName: 'Kochi, Kerala',
      latitude: 9.9312,
      longitude: 76.2673,
      climateType: 'Warm & Humid',
      ambientTemperature: 30.2,
      relativeHumidity: 82,
      atmosphericPressure: 101.2,
      solarRadiation: 680,
      windSpeed: 2.5,
    },
  },
  {
    id: 'composite',
    name: 'Composite (e.g. Delhi)',
    climateType: 'Composite',
    climate: {
      locationName: 'Delhi, NCT',
      latitude: 28.7041,
      longitude: 77.1025,
      climateType: 'Composite',
      ambientTemperature: 26.4,
      relativeHumidity: 45,
      atmosphericPressure: 100.5,
      solarRadiation: 750,
      windSpeed: 2.9,
    },
  },
  {
    id: 'custom',
    name: 'User Defined',
    climateType: 'User Defined',
    climate: {
      locationName: 'Custom Location',
      latitude: 0,
      longitude: 0,
      climateType: 'User Defined',
      ambientTemperature: 20,
      relativeHumidity: 40,
      atmosphericPressure: 101.3,
      solarRadiation: 600,
      windSpeed: 2.0,
    },
  },
];
