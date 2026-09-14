import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, Legend } from 'recharts';
import { Award } from 'lucide-react';
import { Card, SectionHeading, LoadingState, Badge } from '../components/ui';
import { getComparison } from '../api/simulationApi';
import { getMaterialById } from '../mock/materials';
import { ScenarioResult } from '../types';

export default function Comparison() {
  const [scenarios, setScenarios] = useState<ScenarioResult[] | null>(null);

  useEffect(() => {
    getComparison('demo').then(setScenarios);
  }, []);

  if (!scenarios) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Design Comparison" description="Compare baseline, candidate, and recommended designs." />
        <Card><LoadingState message="Loading comparison data..." /></Card>
      </div>
    );
  }

  const chartData = scenarios.map((s) => ({
    name: s.designLabel,
    Comfort: s.comfortPercentage,
    'Heat Loss (kWh)': s.heatLoss,
    'Energy Req. (kWh)': s.externalEnergyRequirement,
  }));

  return (
    <div className="space-y-6">
      <SectionHeading title="Design Comparison" description="Compare baseline, candidate, and recommended designs side by side." />

      <Card title="Comparison Table">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-100">
                <th className="py-2 pr-4 font-medium">Design</th>
                <th className="py-2 pr-4 font-medium">Dimensions (L×W×H)</th>
                <th className="py-2 pr-4 font-medium">Wall Material</th>
                <th className="py-2 pr-4 font-medium">Insulation</th>
                <th className="py-2 pr-4 font-medium">Opening Area</th>
                <th className="py-2 pr-4 font-medium">Comfort</th>
                <th className="py-2 pr-4 font-medium">Heat Loss</th>
                <th className="py-2 pr-4 font-medium">Solar Gain</th>
                <th className="py-2 pr-4 font-medium">External Energy</th>
                <th className="py-2 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => {
                const wall = getMaterialById(s.design.wallMaterialId);
                const insulation = getMaterialById(s.design.insulationMaterialId);
                return (
                  <tr
                    key={s.designId}
                    className={`border-b border-slate-50 last:border-0 ${s.isRecommended ? 'bg-emerald-50/60' : ''}`}
                  >
                    <td className="py-2.5 pr-4 font-medium text-slate-800 flex items-center gap-1.5">
                      {s.isRecommended && <Award size={14} className="text-emerald-600" />}
                      {s.designLabel}
                      {s.isBaseline && <Badge tone="slate">Baseline</Badge>}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-600">{s.design.length}×{s.design.width}×{s.design.height} m</td>
                    <td className="py-2.5 pr-4 text-slate-600">{wall?.name}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{insulation?.name} ({s.design.insulationThickness * 100} cm)</td>
                    <td className="py-2.5 pr-4 text-slate-600">{s.design.openingPercentage}%</td>
                    <td className="py-2.5 pr-4 text-slate-700">{s.comfortPercentage}%</td>
                    <td className="py-2.5 pr-4 text-slate-700">{s.heatLoss} kWh</td>
                    <td className="py-2.5 pr-4 text-slate-700">{s.solarGain} kWh</td>
                    <td className="py-2.5 pr-4 text-slate-700">{s.externalEnergyRequirement} kWh</td>
                    <td className="py-2.5 font-semibold text-slate-900">
                      {s.overallScore}
                      {s.isRecommended && <Badge tone="green">Recommended</Badge>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Comfort, Heat Loss & Energy Requirement" subtitle="Comparison across all evaluated designs">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <RTooltip />
            <Legend />
            <Bar dataKey="Comfort" fill="#2563eb" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Heat Loss (kWh)" fill="#ef4444" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Energy Req. (kWh)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
