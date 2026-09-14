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
import { FileBarChart2, Activity, Sparkles, ThermometerSun, Leaf, Play, Home, Sun, FileText, ArrowRight } from 'lucide-react';
import { Card, StatCard, Badge, ProgressBar, SectionHeading, LoadingState } from '../components/ui';
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
        <Link
          to="/new-analysis"
          className="inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors bg-brand-600 text-white hover:bg-brand-700"
        >
          Start Analysis
        </Link>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        {[
          { to: '/new-analysis', label: 'New Analysis', icon: Home, desc: 'Configure climate, geometry & materials.' },
          { to: '/simulation', label: 'Simulation', icon: Play, desc: 'Run the thermal model and track progress.' },
          { to: '/optimization', label: 'Optimization', icon: Sparkles, desc: 'Auto-search for the best design.' },
          { to: '/report', label: 'Report', icon: FileText, desc: 'Generate a comprehensive final report.' },
        ].map((step, idx) => (
          <Link key={step.to} to={step.to} className="bg-white border border-slate-200 rounded-lg p-4 hover:border-brand-500 hover:shadow-sm transition-all group">
            <div className="flex items-center justify-between mb-3">
              <span className="font-mono text-xs text-slate-400">{String(idx + 1).padStart(2, '0')}</span>
              <step.icon size={18} className="text-brand-600" strokeWidth={1.75} />
            </div>
            <p className="font-semibold text-slate-900 mb-1 text-sm">{step.label}</p>
            <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
            <span className="inline-flex items-center gap-1 text-xs text-brand-600 mt-3 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
              Open <ArrowRight size={12} />
            </span>
          </Link>
        ))}
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
