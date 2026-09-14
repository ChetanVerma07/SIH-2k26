import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, CircleDashed, LoaderCircle, XCircle } from 'lucide-react';
import { Card, ProgressBar, Badge, Button, SectionHeading, EmptyState } from '../components/ui';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { getSimulationStatus, SIMULATION_STAGES, runSimulation } from '../api/simulationApi';
import { ShelterVisualization } from '../components/ShelterVisualization';

export default function SimulationPage() {
  const navigate = useNavigate();
  const { project, simulation, setSimulation } = useAnalysis();
  const [failed, setFailed] = useState(false);
  const runningRef = useRef(false);

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

  return (
    <div className="space-y-6 max-w-3xl">
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
            {simulation.status === 'Completed' && (
              <Button onClick={() => navigate('/results')}>View Results</Button>
            )}
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
    </div>
  );
}
