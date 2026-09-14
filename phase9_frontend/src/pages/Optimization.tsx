import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { Cpu, Target, Layers, Trophy } from 'lucide-react';
import { Card, StatCard, SectionHeading, LoadingState, Badge } from '../components/ui';
import { getOptimizationResults } from '../api/simulationApi';
import { OptimizationResult } from '../types';

const RANK_COLORS = ['#16a34a', '#2563eb', '#0ea5e9', '#f59e0b', '#94a3b8'];

export default function Optimization() {
  const [opt, setOpt] = useState<OptimizationResult | null>(null);

  useEffect(() => {
    getOptimizationResults('demo').then(setOpt);
  }, []);

  if (!opt) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Optimization" description="Algorithm convergence, top candidates, and sensitivity analysis." />
        <Card><LoadingState message="Loading optimization results..." /></Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeading title="Optimization" description="Algorithm convergence, top candidates, and sensitivity analysis." />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Algorithm" value={opt.algorithm} icon={Cpu} tone="blue" />
        <StatCard label="Candidates Evaluated" value={opt.candidatesEvaluated} icon={Layers} tone="slate" />
        <StatCard label="Generations" value={opt.generations} icon={Target} tone="amber" />
        <StatCard label="Best Score" value={opt.bestScore} icon={Trophy} tone="green" />
      </div>

      <Card title="Optimization Convergence" subtitle="Best and average score per generation">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={opt.convergence} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="generation" tick={{ fontSize: 11 }} label={{ value: 'Generation', position: 'insideBottom', offset: -2, fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: 'Score', angle: -90, position: 'insideLeft', fontSize: 11 }} domain={[0, 100]} />
            <RTooltip />
            <Legend />
            <Line type="monotone" dataKey="bestScore" name="Best Score" stroke="#16a34a" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="averageScore" name="Average Score" stroke="#94a3b8" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Top 5 Designs" subtitle="Ranked by overall optimization score">
          <ol className="space-y-3">
            {opt.topDesigns.map((d, i) => (
              <li key={d.designId} className="flex items-center justify-between border border-slate-100 rounded-md px-3 py-2.5">
                <div className="flex items-center gap-3">
                  <span
                    className="h-6 w-6 rounded-full flex items-center justify-center text-xs font-semibold text-white"
                    style={{ backgroundColor: RANK_COLORS[i % RANK_COLORS.length] }}
                  >
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{d.designLabel}</p>
                    <p className="text-xs text-slate-500">Comfort {d.comfortPercentage}% · Energy {d.externalEnergyRequirement} kWh</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {d.isRecommended && <Badge tone="green">Recommended</Badge>}
                  <span className="font-semibold text-slate-900">{d.overallScore}</span>
                </div>
              </li>
            ))}
          </ol>
        </Card>

        <Card title="Sensitivity Analysis" subtitle="Relative importance of design factors on overall score">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={opt.sensitivity} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" domain={[0, 0.4]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="factor" width={140} tick={{ fontSize: 11 }} />
              <RTooltip formatter={(v: number) => `${Math.round(v * 100)}%`} />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {opt.sensitivity.map((_, i) => (
                  <Cell key={i} fill={RANK_COLORS[i % RANK_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
