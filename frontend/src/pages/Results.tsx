import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Thermometer, Sun, Flame, Zap, Gauge, TrendingDown } from 'lucide-react';
import { Card, StatCard, SectionHeading, Button, EmptyState, LoadingState } from '../components/ui';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { getSimulationResults } from '../api/simulationApi';
import { SimulationResult, TimeSeriesPoint, HeatFlowBreakdown as HeatFlowBreakdownType } from '../types';

import { TemperatureChart } from '../components/TemperatureChart';
import { EnergyChart } from '../components/EnergyChart';
import { HeatFlowBreakdown } from '../components/HeatFlowBreakdown';
import { ThermalComfort } from '../components/ThermalComfort';

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

  const seriesData: TimeSeriesPoint[] = result.hourly.map((h) => ({
    hour: h.hour,
    ambientTempC: h.outdoorTemp,
    indoorTempC: h.indoorTemp,
    solarGainW: h.solarRadiation * 2, // approximated area factor
    wallLossW: h.heatLoss * 0.40,
    roofLossW: h.heatLoss * 0.35,
    floorLossW: h.heatLoss * 0.10,
    openingLossW: h.heatLoss * 0.15,
    totalLossW: h.heatLoss,
  }));

  const heatFlowBreakdownData: HeatFlowBreakdownType = {
    walls: result.heatLoss * 1000 * 0.40,
    roof: result.heatLoss * 1000 * 0.35,
    floor: result.heatLoss * 1000 * 0.10,
    openings: result.heatLoss * 1000 * 0.15,
  };

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
        <TemperatureChart series={seriesData} />
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Energy Performance" subtitle="Thermal losses and solar heat gains over 24 hours">
          <EnergyChart series={seriesData} />
        </Card>

        <Card title="Heat Flow Breakdown" subtitle="Relative contribution to total envelope heat loss">
          <HeatFlowBreakdown breakdown={heatFlowBreakdownData} />
        </Card>
      </div>

      <Card title="Thermal Comfort Range" subtitle={`${result.comfortPercentage}% of the simulated period falls within ${result.comfortBandMin}–${result.comfortBandMax} °C`}>
        <ThermalComfort 
          comfortMin={result.comfortBandMin} 
          comfortMax={result.comfortBandMax} 
          onChangeMin={() => {}} 
          onChangeMax={() => {}} 
          result={result} 
        />
      </Card>

      <div className="flex gap-3 pb-6">
        <Button onClick={() => navigate('/optimization')}>View Optimization</Button>
        <Button variant="secondary" onClick={() => navigate('/designs')}>Compare Designs</Button>
      </div>
    </div>
  );
}
