import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, CircleDashed, LoaderCircle, XCircle, Award, ArrowRight, LayoutGrid } from 'lucide-react';
import { Card, ProgressBar, Badge, Button, SectionHeading, EmptyState } from '../components/ui';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { getSimulationStatus, SIMULATION_STAGES, runSimulation } from '../api/simulationApi';
import { ShelterVisualization, ShelterGeometry } from '../components/ShelterVisualization';
import { getComparison } from '../api/simulationApi';
import { ScenarioResult } from '../types';
import { getMaterialById } from '../mock/materials';

export default function SimulationPage() {
  const navigate = useNavigate();
  const { project, simulation, setSimulation, draft, setDraft, setProject } = useAnalysis();
  const [failed, setFailed] = useState(false);
  const runningRef = useRef(false);
  const [aiDesigns, setAiDesigns] = useState<ScenarioResult[] | null>(null);

  useEffect(() => {
    if (!simulation || simulation.status === 'Completed' || simulation.status === 'Failed') return;
    if (runningRef.current) return;
    runningRef.current = true;

    let cancelled = false;
    async function tick(current = simulation!) {
      try {
        const updated = await getSimulationStatus(current);
        if (cancelled) return;
        setSimulation(updated);
        if (updated.status === 'Completed' || updated.status === 'Failed') {
          runningRef.current = false;
          if (updated.status === 'Failed') setFailed(true);
          return;
        }
        tick(updated);
      } catch (err) {
        if (cancelled) return;
        setFailed(true);
        setSimulation({ ...current, status: 'Failed' });
        runningRef.current = false;
      }
    }
    tick();
    return () => {
      cancelled = true;
      runningRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [simulation?.id]);

  // Load AI designs when simulation completes
  useEffect(() => {
    if (simulation?.status === 'Completed') {
      getComparison('demo').then((scenarios) => {
        // Get top 3 designs sorted by score, with recommended first
        const sorted = [...scenarios].sort((a, b) => {
          if (a.isRecommended && !b.isRecommended) return -1;
          if (!a.isRecommended && b.isRecommended) return 1;
          return b.overallScore - a.overallScore;
        });
        setAiDesigns(sorted.slice(0, 3));
      });
    }
  }, [simulation?.status]);

  if (!project || !simulation) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Simulation" description="Track the status of your thermal simulation run." />
        <Card>
          <EmptyState
            title="No active simulation"
            message="Start a new analysis to launch a simulation run."
            action={<Button onClick={() => navigate('/new-analysis')}>New Analysis</Button>}
          />
        </Card>
      </div>
    );
  }

  const currentIndex = SIMULATION_STAGES.indexOf(simulation.currentStage);

  const mapDesignToGeometry = (design: any): ShelterGeometry => ({
    lengthM: design.length,
    widthM: design.width,
    heightM: design.height,
    wallThicknessM: design.wallThickness,
    roofType: design.roofMaterialId.includes('timber') ? 'pitched' : 'flat',
    orientation: design.orientation.replace(/outh|orth|ast|est|-/g, ''),
    windowAreaM2: (design.length * design.height * design.openingPercentage) / 100,
    doorAreaM2: 2,
  });

  const handleSelectDesign = (scenario: ScenarioResult) => {
    setDraft((d) => ({ ...d, design: scenario.design }));
    const nextProject = project
      ? { ...project, design: scenario.design }
      : {
          id: `project-${scenario.design.id}`,
          name: draft.name,
          createdAt: new Date().toISOString(),
          climate: draft.climate,
          requirements: draft.requirements,
          design: scenario.design,
          designMode: draft.designMode,
          status: 'completed' as const,
        };
    setProject(nextProject);
  };

  return (
    <div className="space-y-6">
      <SectionHeading title="Simulation" description="Track the status of your thermal simulation run." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-xs text-slate-500">Simulation ID</p>
              <p className="font-mono text-sm text-slate-800 truncate">{simulation.id}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge tone="amber">DEMO SIMULATION</Badge>
              <Badge tone={simulation.status === 'Completed' ? 'green' : simulation.status === 'Failed' ? 'red' : 'blue'}>
                {simulation.status}
              </Badge>
            </div>
          </div>

          <div className="mb-6">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-600">Overall progress</span>
              <span className="font-medium text-slate-800">{simulation.progress}%</span>
            </div>
            <ProgressBar value={simulation.progress} tone={simulation.status === 'Completed' ? 'green' : 'blue'} />
          </div>

          <ol className="space-y-3">
            {SIMULATION_STAGES.map((stage, i) => {
              const done = i < currentIndex || simulation.status === 'Completed';
              const active = i === currentIndex && simulation.status === 'Running';
              return (
                <li key={stage} className="flex items-center gap-3 text-sm">
                  {done ? (
                    <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />
                  ) : active ? (
                    <LoaderCircle size={18} className="text-brand-600 shrink-0 animate-spin" />
                  ) : (
                    <CircleDashed size={18} className="text-slate-300 shrink-0" />
                  )}
                  <span className={done || active ? 'text-slate-800 font-medium' : 'text-slate-400'}>{stage}</span>
                </li>
              );
            })}
          </ol>

          <p className="text-xs text-slate-400 mt-6">
            This simulation is a scripted demo sequence and does not invoke a real ANSYS or CFD solver.
          </p>

          <div className="mt-6 flex gap-3">
            {simulation.status === 'Failed' && (
              <Button
                variant="secondary"
                onClick={async () => {
                  try {
                    const s = await runSimulation(project.id);
                    setSimulation(s);
                    setFailed(false);
                  } catch (err) {
                    setFailed(true);
                    if (simulation) setSimulation({ ...simulation, status: 'Failed' });
                  }
                }}
              >
                Retry Simulation
              </Button>
            )}
          </div>
        </Card>

        {project.design && (
          <Card className="flex flex-col h-full bg-slate-900 border-slate-800 text-slate-200">
            <div className="mb-2">
              <h3 className="font-medium text-sm text-slate-200 mb-1">Thermal Simulation Model</h3>
              <p className="text-xs text-slate-400">Real-time geometric evaluation mesh</p>
            </div>
            <div className="flex-1 flex items-center justify-center min-h-[300px]">
              <ShelterVisualization
                geometry={{
                  lengthM: project.design.length,
                  widthM: project.design.width,
                  heightM: project.design.height,
                  wallThicknessM: project.design.wallThickness,
                  roofType: project.design.roofMaterialId.includes('timber') ? 'pitched' : 'flat',
                  orientation: project.design.orientation.replace(/outh|orth|ast|est|-/g, ''),
                  windowAreaM2: (project.design.length * project.design.height * project.design.openingPercentage) / 100,
                  doorAreaM2: 2,
                }}
                isSimulating={simulation.status === 'Running'}
              />
            </div>
          </Card>
        )}
      </div>

      {failed && (
        <Card>
          <div className="flex items-center gap-3 text-red-600 text-sm">
            <XCircle size={18} /> Simulation failed. This can happen with invalid geometry or missing climate data.
          </div>
        </Card>
      )}

      {/* AI Best Pick Designs — shown after simulation completes */}
      {simulation.status === 'Completed' && aiDesigns && aiDesigns.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Award size={20} className="text-emerald-500" />
            <h3 className="text-base font-semibold text-slate-800">AI Best Pick — Recommended Designs</h3>
            <Badge tone="green">Top 3</Badge>
          </div>

          <div className="grid lg:grid-cols-3 gap-5">
            {aiDesigns.map((s) => {
              const wall = getMaterialById(s.design.wallMaterialId);
              const insulation = getMaterialById(s.design.insulationMaterialId);
              const isSelected = draft.design.id === s.design.id || project?.design.id === s.design.id;

              return (
                <Card
                  key={s.designId}
                  className={`transition-all duration-300 relative overflow-hidden ${
                    isSelected ? 'ring-2 ring-brand-500 shadow-md' : 'hover:border-brand-300'
                  }`}
                >
                  {s.isRecommended && (
                    <div className="absolute top-0 right-0 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 uppercase tracking-wider rounded-bl-lg z-20 flex items-center gap-1">
                      <Award size={12} /> AI Best Pick
                    </div>
                  )}
                  {isSelected && (
                    <div className="absolute top-0 left-0 bg-brand-500 text-white text-[10px] font-bold px-3 py-1 uppercase tracking-wider rounded-br-lg z-20 flex items-center gap-1">
                      <CheckCircle2 size={12} /> Selected
                    </div>
                  )}

                  {/* 3D Preview */}
                  <div className="h-48 relative rounded-lg overflow-hidden bg-slate-950/80 mb-3 -mx-5 -mt-5">
                    <ShelterVisualization
                      geometry={mapDesignToGeometry(s.design)}
                      isSimulating={false}
                    />
                  </div>

                  {/* Info */}
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-1">{s.designLabel}</h4>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge tone={s.overallScore > 80 ? 'green' : s.overallScore > 60 ? 'amber' : 'slate'}>
                        {s.overallScore}% Score
                      </Badge>
                      <Badge tone="blue">{s.design.orientation}</Badge>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Dimensions</span>
                        <span className="font-medium text-slate-700">{s.design.length}m × {s.design.width}m</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Comfort</span>
                        <span className="font-medium text-emerald-600">{s.comfortPercentage}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Heat Loss</span>
                        <span className="font-medium text-red-500">{s.heatLoss} kWh</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <Button
                      variant={isSelected ? 'secondary' : 'primary'}
                      className="w-full text-xs"
                      onClick={() => handleSelectDesign(s)}
                    >
                      {isSelected ? 'Currently Selected' : 'Select This Design'}
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Action buttons row */}
          <div className="flex items-center gap-3 pt-2">
            <Button
              variant="secondary"
              onClick={() => navigate('/designs')}
              className="gap-2"
            >
              <LayoutGrid size={16} />
              Choose from Another Design
            </Button>
            <Button
              onClick={() => navigate('/results')}
              className="gap-2"
            >
              View Result
              <ArrowRight size={16} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
