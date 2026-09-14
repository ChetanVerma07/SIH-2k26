import React, { useEffect, useState } from 'react';
import { Download, Printer, FileJson, FileSpreadsheet } from 'lucide-react';
import { Card, SectionHeading, Button, LoadingState, Badge } from '../components/ui';
import { getReport } from '../api/simulationApi';
import { getMaterialById } from '../mock/materials';
import { Report as ReportType } from '../types';

function downloadFile(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function reportToCsv(report: ReportType): string {
  const rows: string[][] = [
    ['Section', 'Field', 'Value'],
    ['Project', 'Name', report.project.name],
    ['Project', 'Status', report.project.status],
    ['Climate', 'Location', report.project.climate.locationName],
    ['Climate', 'Type', report.project.climate.climateType],
    ['Climate', 'Ambient Temp (C)', String(report.project.climate.ambientTemperature)],
    ['Design', 'Dimensions (L x W x H, m)', `${report.project.design.length} x ${report.project.design.width} x ${report.project.design.height}`],
    ['Design', 'Orientation', report.project.design.orientation],
    ['Performance', 'Average Indoor Temp (C)', String(report.simulationResult.averageIndoorTemp)],
    ['Performance', 'Comfort Percentage (%)', String(report.simulationResult.comfortPercentage)],
    ['Performance', 'Heat Loss (kWh)', String(report.simulationResult.heatLoss)],
    ['Performance', 'Solar Gain (kWh)', String(report.simulationResult.solarGain)],
    ['Performance', 'External Energy Requirement (kWh)', String(report.simulationResult.externalEnergyRequirement)],
    ['Optimization', 'Algorithm', report.optimizationResult.algorithm],
    ['Optimization', 'Best Score', String(report.optimizationResult.bestScore)],
    ['Recommendation', 'Design', report.recommendation.design.label],
  ];
  return rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n');
}

export default function ReportPage() {
  const [report, setReport] = useState<ReportType | null>(null);

  useEffect(() => {
    getReport('demo').then(setReport);
  }, []);

  if (!report) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Report" description="Structured engineering report for the analysis." />
        <Card><LoadingState message="Generating report..." /></Card>
      </div>
    );
  }

  const { project, recommendation, simulationResult, optimizationResult, comparison } = report;
  const wall = getMaterialById(project.design.wallMaterialId);
  const insulation = getMaterialById(project.design.insulationMaterialId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <SectionHeading title="Report" description="Structured engineering report for the analysis." />
        <div className="flex gap-2 print:hidden">
          <Button variant="secondary" onClick={() => downloadFile(`${project.name}.json`, JSON.stringify(report, null, 2), 'application/json')}>
            <FileJson size={16} /> Export JSON
          </Button>
          <Button variant="secondary" onClick={() => downloadFile(`${project.name}.csv`, reportToCsv(report), 'text/csv')}>
            <FileSpreadsheet size={16} /> Export CSV
          </Button>
          <Button onClick={() => window.print()}>
            <Printer size={16} /> Print Report
          </Button>
        </div>
      </div>

      <Card title="Project" action={<Badge tone="green">{project.status}</Badge>}>
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <RowStat label="Name" value={project.name} />
          <RowStat label="Created" value={new Date(project.createdAt).toLocaleDateString()} />
          <RowStat label="Design Mode" value={project.designMode.replace('_', ' ')} />
        </div>
      </Card>

      <Card title="Location & Climate">
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <RowStat label="Location" value={project.climate.locationName} />
          <RowStat label="Climate Type" value={project.climate.climateType} />
          <RowStat label="Ambient Temp." value={`${project.climate.ambientTemperature} °C`} />
          <RowStat label="Humidity" value={`${project.climate.relativeHumidity}%`} />
          <RowStat label="Solar Radiation" value={`${project.climate.solarRadiation} W/m²`} />
          <RowStat label="Wind Speed" value={`${project.climate.windSpeed} m/s`} />
        </div>
      </Card>

      <Card title="Shelter Design & Materials">
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <RowStat label="Dimensions" value={`${project.design.length} × ${project.design.width} × ${project.design.height} m`} />
          <RowStat label="Orientation" value={project.design.orientation} />
          <RowStat label="Opening Area" value={`${project.design.openingPercentage}%`} />
          <RowStat label="Wall Material" value={wall?.name ?? '—'} />
          <RowStat label="Insulation" value={`${insulation?.name ?? '—'} (${project.design.insulationThickness * 100} cm)`} />
          <RowStat label="Floor Area (req.)" value={`${project.requirements.floorArea} m²`} />
        </div>
      </Card>

      <Card title="Simulation & Performance">
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <RowStat label="Average Indoor Temp." value={`${simulationResult.averageIndoorTemp} °C`} />
          <RowStat label="Comfort" value={`${simulationResult.comfortPercentage}%`} />
          <RowStat label="Heat Loss" value={`${simulationResult.heatLoss} kWh`} />
          <RowStat label="Solar Gain" value={`${simulationResult.solarGain} kWh`} />
          <RowStat label="External Energy Requirement" value={`${simulationResult.externalEnergyRequirement} kWh`} />
        </div>
      </Card>

      <Card title="Optimization Summary">
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <RowStat label="Algorithm" value={optimizationResult.algorithm} />
          <RowStat label="Candidates Evaluated" value={String(optimizationResult.candidatesEvaluated)} />
          <RowStat label="Best Score" value={String(optimizationResult.bestScore)} />
        </div>
      </Card>

      <Card title="Design Comparison Summary">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-100">
                <th className="py-2 pr-4 font-medium">Design</th>
                <th className="py-2 pr-4 font-medium">Comfort</th>
                <th className="py-2 pr-4 font-medium">Heat Loss</th>
                <th className="py-2 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((c) => (
                <tr key={c.designId} className="border-b border-slate-50 last:border-0">
                  <td className="py-2 pr-4 font-medium text-slate-800">{c.designLabel}</td>
                  <td className="py-2 pr-4 text-slate-600">{c.comfortPercentage}%</td>
                  <td className="py-2 pr-4 text-slate-600">{c.heatLoss} kWh</td>
                  <td className="py-2 font-semibold text-slate-900">{c.overallScore}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Recommendation">
        <p className="text-sm text-slate-700 leading-relaxed mb-3">{recommendation.explanation}</p>
        <p className="text-xs font-medium text-slate-500 mb-1">Assumptions</p>
        <ul className="text-sm text-slate-600 list-disc list-inside mb-3">
          {recommendation.assumptions.map((a, i) => <li key={i}>{a}</li>)}
        </ul>
        <p className="text-xs font-medium text-slate-500 mb-1">Limitations</p>
        <ul className="text-sm text-slate-600 list-disc list-inside">
          {recommendation.limitations.map((a, i) => <li key={i}>{a}</li>)}
        </ul>
      </Card>

      <p className="text-xs text-slate-400 pb-6">Report generated {new Date(report.generatedAt).toLocaleString()} — demo data, not a certified engineering report.</p>
    </div>
  );
}

function RowStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}
