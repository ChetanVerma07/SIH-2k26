import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertTriangle, ListChecks, Award } from 'lucide-react';
import { Card, SectionHeading, LoadingState, Badge, StatCard } from '../components/ui';
import { getRecommendation } from '../api/simulationApi';
import { getMaterialById } from '../mock/materials';
import { Recommendation as RecommendationType } from '../types';
import { Thermometer, Sun, Zap, TrendingDown } from 'lucide-react';

export default function Recommendation() {
  const [rec, setRec] = useState<RecommendationType | null>(null);

  useEffect(() => {
    getRecommendation('demo').then(setRec);
  }, []);

  if (!rec) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Recommendation" description="Final recommended passive shelter design." />
        <Card><LoadingState message="Loading recommendation..." /></Card>
      </div>
    );
  }

  const { design } = rec;
  const wall = getMaterialById(design.wallMaterialId);
  const roof = getMaterialById(design.roofMaterialId);
  const floor = getMaterialById(design.floorMaterialId);
  const insulation = getMaterialById(design.insulationMaterialId);

  return (
    <div className="space-y-6">
      <SectionHeading title="Recommendation" description="Final recommended passive shelter design based on simulation and optimization results." />

      <Card className="border-emerald-200">
        <div className="flex items-center gap-3 mb-1">
          <Award className="text-emerald-600" size={22} />
          <h3 className="text-xl font-semibold text-slate-900">Recommended Passive Shelter</h3>
          <Badge tone="green">Top Ranked Design</Badge>
        </div>
        <p className="text-sm text-slate-500">{design.label} · {design.orientation}-facing orientation</p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
          <SpecRow label="Length" value={`${design.length} m`} />
          <SpecRow label="Width" value={`${design.width} m`} />
          <SpecRow label="Height" value={`${design.height} m`} />
          <SpecRow label="Orientation" value={design.orientation} />
          <SpecRow label="Wall" value={`${wall?.name} (${design.wallThickness * 100} cm)`} />
          <SpecRow label="Roof" value={`${roof?.name} (${design.roofThickness * 100} cm)`} />
          <SpecRow label="Floor" value={`${floor?.name} (${design.floorThickness * 100} cm)`} />
          <SpecRow label="Insulation" value={`${insulation?.name} (${design.insulationThickness * 100} cm)`} />
          <SpecRow label="Opening Area" value={`${design.openingPercentage}%`} />
        </div>
      </Card>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Thermal Comfort" value={rec.performance.comfort} unit="%" icon={Thermometer} tone="green" />
        <StatCard label="Heat Loss" value={rec.performance.heatLoss} unit="kWh" icon={TrendingDown} tone="red" />
        <StatCard label="Solar Gain" value={rec.performance.solarGain} unit="kWh" icon={Sun} tone="amber" />
        <StatCard label="External Energy Req." value={rec.performance.externalEnergyRequirement} unit="kWh" icon={Zap} tone="blue" />
      </div>

      <Card title="Why this design?">
        <div className="flex gap-3">
          <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-slate-700 leading-relaxed">{rec.explanation}</p>
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card title="Trade-offs" >
          <ul className="space-y-2 text-sm text-slate-600">
            {rec.tradeoffs.map((t, i) => (
              <li key={i} className="flex gap-2"><ListChecks size={15} className="text-slate-400 shrink-0 mt-0.5" />{t}</li>
            ))}
          </ul>
        </Card>
        <Card title="Assumptions">
          <ul className="space-y-2 text-sm text-slate-600">
            {rec.assumptions.map((t, i) => (
              <li key={i} className="flex gap-2"><ListChecks size={15} className="text-slate-400 shrink-0 mt-0.5" />{t}</li>
            ))}
          </ul>
        </Card>
        <Card title="Limitations">
          <ul className="space-y-2 text-sm text-slate-600">
            {rec.limitations.map((t, i) => (
              <li key={i} className="flex gap-2"><AlertTriangle size={15} className="text-amber-500 shrink-0 mt-0.5" />{t}</li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

function SpecRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-slate-100 pb-1.5 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}
