import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { FileBarChart2, Activity, Sparkles, ThermometerSun, Leaf } from 'lucide-react';
import { Card, StatCard, Badge, ProgressBar, SectionHeading, LoadingState, Button } from '../components/ui';
import { getRecentAnalyses } from '../api/analysisApi';
import { getClimate } from '../api/climateApi';
import { SIMULATION_RESULT } from '../mock/designs';
import { RECOMMENDED_DESIGN } from '../mock/designs';
import { ClimateData } from '../types';

export default function Dashboard() {
  const [recent, setRecent] = useState<Awaited<ReturnType<typeof getRecentAnalyses>> | null>(null);
  const [climate, setClimate] = useState<ClimateData | null>(null);

  useEffect(() => {
    getRecentAnalyses().then(setRecent);
    getClimate('ladakh').then(setClimate);
  }, []);

  const chartData = SIMULATION_RESULT.hourly.map((h) => ({
    hour: `${h.hour}:00`,
    Indoor: h.indoorTemp,
    Outdoor: h.outdoorTemp,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <SectionHeading
          title="Dashboard"
          description="Overview of analyses, simulations, and optimization activity."
        />
        <Link to="/new-analysis">
          <Button>New Analysis</Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatCard label="Total Analyses" value={24} icon={FileBarChart2} tone="blue" />
        <StatCard label="Simulations Completed" value={19} icon={Activity} tone="green" />
        <StatCard label="Optimized Designs" value={11} icon={Sparkles} tone="amber" />
        <StatCard label="Avg. Thermal Comfort" value={78} unit="%" icon={ThermometerSun} tone="blue" />
        <StatCard label="Est. Energy Savings" value={42} unit="%" icon={Leaf} tone="green" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card
          title="Thermal Performance — Latest Recommended Design"
          subtitle="Indoor vs outdoor temperature over a representative 24-hour cycle (Leh, Ladakh)"
          className="xl:col-span-2"
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: '°C', angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <RTooltip />
              <Legend />
              <Line type="monotone" dataKey="Indoor" stroke="#2563eb" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Outdoor" stroke="#94a3b8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <div className="space-y-6">
          <Card title="Current Climate Summary">
            {climate ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">Location</span><span className="font-medium text-slate-800">{climate.locationName}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Climate Type</span><Badge tone="blue">{climate.climateType}</Badge></div>
                <div className="flex justify-between"><span className="text-slate-500">Ambient Temp.</span><span className="font-medium text-slate-800">{climate.ambientTemperature} °C</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Humidity</span><span className="font-medium text-slate-800">{climate.relativeHumidity}%</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Wind Speed</span><span className="font-medium text-slate-800">{climate.windSpeed} m/s</span></div>
              </div>
            ) : (
              <LoadingState message="Loading climate summary..." />
            )}
          </Card>

          <Card title="Latest Recommended Design">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Dimensions</span><span className="font-medium text-slate-800">{RECOMMENDED_DESIGN.length}×{RECOMMENDED_DESIGN.width}×{RECOMMENDED_DESIGN.height} m</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Orientation</span><span className="font-medium text-slate-800">{RECOMMENDED_DESIGN.orientation}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Insulation</span><span className="font-medium text-slate-800">{RECOMMENDED_DESIGN.insulationThickness * 100} cm</span></div>
              <Link to="/recommendation" className="inline-block mt-1 text-brand-600 text-sm font-medium hover:underline">
                View full recommendation →
              </Link>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card title="Recent Analyses" action={<Badge tone="slate">Demo Data</Badge>}>
          {recent ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-100">
                    <th className="py-2 pr-3 font-medium">Name</th>
                    <th className="py-2 pr-3 font-medium">Location</th>
                    <th className="py-2 pr-3 font-medium">Date</th>
                    <th className="py-2 pr-3 font-medium">Comfort</th>
                    <th className="py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((r) => (
                    <tr key={r.id} className="border-b border-slate-50 last:border-0">
                      <td className="py-2.5 pr-3 font-medium text-slate-800">{r.name}</td>
                      <td className="py-2.5 pr-3 text-slate-600">{r.location}</td>
                      <td className="py-2.5 pr-3 text-slate-500">{r.date}</td>
                      <td className="py-2.5 pr-3 text-slate-700">{r.comfort}%</td>
                      <td className="py-2.5"><Badge tone="green">{r.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <LoadingState message="Loading recent analyses..." />
          )}
        </Card>

        <Card title="Optimization Progress" subtitle="Current generation vs best score">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Generation 10 / 10</span>
                <span className="font-medium text-slate-800">Best score: 91</span>
              </div>
              <ProgressBar value={100} tone="green" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Candidates Evaluated</span>
                <span className="font-medium text-slate-800">480</span>
              </div>
              <ProgressBar value={100} tone="blue" />
            </div>
            <Link to="/optimization" className="inline-block text-brand-600 text-sm font-medium hover:underline">
              View optimization details →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
