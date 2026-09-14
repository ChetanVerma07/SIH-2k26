import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Legend,
  ReferenceArea,
} from 'recharts';
import { Thermometer, Sun, Flame, Zap, Gauge, TrendingDown } from 'lucide-react';
import { Card, StatCard, SectionHeading, Button, EmptyState, LoadingState } from '../components/ui';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { getSimulationResults } from '../api/simulationApi';
import { SimulationResult } from '../types';

export default function Results() {
  const navigate = useNavigate();
  const { simulation } = useAnalysis();
  const [result, setResult] = useState<SimulationResult | null>(null);

  useEffect(() => {
    if (simulation?.status === 'Completed') {
      getSimulationResults(simulation.id).then(setResult);
    }
  }, [simulation]);

  if (!simulation || simulation.status !== 'Completed') {
    return (
      <div className="space-y-6">
        <SectionHeading title="Results" description="Thermal performance results for the completed simulation." />
        <Card>
          <EmptyState
            title="No results available"
            message="Run and complete a simulation first to see thermal performance results."
            action={<Button onClick={() => navigate('/new-analysis')}>Start New Analysis</Button>}
          />
        </Card>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Results" description="Thermal performance results for the completed simulation." />
        <Card><LoadingState message="Loading results..." /></Card>
      </div>
    );
  }

  const tempData = result.hourly.map((h) => ({ hour: `${h.hour}:00`, Indoor: h.indoorTemp, Outdoor: h.outdoorTemp }));
  const solarData = result.hourly.map((h) => ({ hour: `${h.hour}:00`, Solar: h.solarRadiation }));
  const heatLossData = result.hourly.map((h) => ({ hour: `${h.hour}:00`, 'Heat Loss': h.heatLoss }));

  return (
    <div className="space-y-6">
      <SectionHeading title="Results" description="Detailed thermal performance for the recommended shelter design." />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Average Indoor Temp." value={result.averageIndoorTemp} unit="°C" icon={Thermometer} tone="blue" />
        <StatCard label="Min Temp." value={result.minIndoorTemp} unit="°C" icon={Thermometer} tone="slate" />
        <StatCard label="Max Temp." value={result.maxIndoorTemp} unit="°C" icon={Thermometer} tone="slate" />
        <StatCard label="Comfort Percentage" value={result.comfortPercentage} unit="%" icon={Gauge} tone="green" />
        <StatCard label="Heat Loss" value={result.heatLoss} unit="kWh" icon={TrendingDown} tone="red" />
        <StatCard label="Solar Gain" value={result.solarGain} unit="kWh" icon={Sun} tone="amber" />
        <StatCard label="External Energy Req." value={result.externalEnergyRequirement} unit="kWh" icon={Zap} tone="blue" />
        <StatCard label="Comfort Band" value={`${result.comfortBandMin}–${result.comfortBandMax}`} unit="°C" icon={Flame} tone="slate" />
      </div>

      <Card
        title="Indoor vs Outdoor Temperature"
        subtitle="Shaded band shows the target thermal comfort range"
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={tempData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', fontSize: 11 }} />
            <RTooltip />
            <Legend />
            <ReferenceArea y1={result.comfortBandMin} y2={result.comfortBandMax} fill="#22c55e" fillOpacity={0.08} label={{ value: 'Comfort Band', position: 'insideTopLeft', fontSize: 10, fill: '#16a34a' }} />
            <Line type="monotone" dataKey="Indoor" stroke="#2563eb" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Outdoor" stroke="#94a3b8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Solar Radiation vs Time" subtitle="Incident solar radiation over 24 hours (W/m²)">
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={solarData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: 'W/m²', angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <RTooltip />
              <Area type="monotone" dataKey="Solar" stroke="#f59e0b" fill="#fde68a" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Heat Loss Over Time" subtitle="Estimated envelope heat loss (W)">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={heatLossData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: 'Watts', angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <RTooltip />
              <Line type="monotone" dataKey="Heat Loss" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Thermal Comfort Range" subtitle={`${result.comfortPercentage}% of the simulated period falls within ${result.comfortBandMin}–${result.comfortBandMax} °C`}>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={tempData} margin={{ top: 5, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={2} />
            <YAxis tick={{ fontSize: 11 }} domain={['dataMin - 5', 'dataMax + 5']} />
            <RTooltip />
            <ReferenceArea y1={result.comfortBandMin} y2={result.comfortBandMax} fill="#22c55e" fillOpacity={0.12} />
            <Line type="monotone" dataKey="Indoor" stroke="#2563eb" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="flex gap-3 pb-6">
        <Button onClick={() => navigate('/optimization')}>View Optimization</Button>
        <Button variant="secondary" onClick={() => navigate('/designs')}>Compare Designs</Button>
      </div>
    </div>
  );
}
