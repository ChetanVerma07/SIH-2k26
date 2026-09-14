import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Card, SectionHeading, Select, LoadingState, Badge } from '../components/ui';
import { getClimate, getClimateProfile } from '../api/climateApi';
import { CLIMATE_PRESETS } from '../mock/climate';
import { ClimateData, ClimateProfile } from '../types';

export default function Climate() {
  const [presetId, setPresetId] = useState('ladakh');
  const [climate, setClimate] = useState<ClimateData | null>(null);
  const [profile, setProfile] = useState<ClimateProfile | null>(null);

  useEffect(() => {
    getClimate(presetId).then(setClimate);
    getClimateProfile(presetId).then(setProfile);
  }, [presetId]);

  const chartData = profile?.points.map((p) => ({
    hour: `${p.hour}:00`,
    Temperature: p.temperature,
    Humidity: p.humidity,
    Pressure: p.pressure,
    Solar: p.solarRadiation,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <SectionHeading title="Climate" description="Location climate conditions and 24-hour profiles." />
        <Select value={presetId} onChange={(e) => setPresetId(e.target.value)} aria-label="Select climate preset">
          {CLIMATE_PRESETS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </Select>
      </div>

      {!climate || !profile ? (
        <Card><LoadingState message="Loading climate data..." /></Card>
      ) : (
        <>
          <Card title="Current Conditions" action={<Badge tone="blue">{climate.climateType}</Badge>}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
              <Stat label="Location" value={climate.locationName} />
              <Stat label="Ambient Temp." value={`${climate.ambientTemperature} °C`} />
              <Stat label="Humidity" value={`${climate.relativeHumidity}%`} />
              <Stat label="Pressure" value={`${climate.atmosphericPressure} kPa`} />
              <Stat label="Wind Speed" value={`${climate.windSpeed} m/s`} />
            </div>
          </Card>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card title="Temperature" subtitle="24-hour profile (°C)">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <RTooltip />
                  <Line type="monotone" dataKey="Temperature" stroke="#2563eb" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Humidity" subtitle="24-hour profile (%)">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <RTooltip />
                  <Area type="monotone" dataKey="Humidity" stroke="#0ea5e9" fill="#bae6fd" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Pressure" subtitle="24-hour profile (kPa)">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
                  <YAxis tick={{ fontSize: 11 }} domain={['dataMin - 1', 'dataMax + 1']} />
                  <RTooltip />
                  <Line type="monotone" dataKey="Pressure" stroke="#64748b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Solar Radiation" subtitle="24-hour profile (W/m²)">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <RTooltip />
                  <Area type="monotone" dataKey="Solar" stroke="#f59e0b" fill="#fde68a" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}
