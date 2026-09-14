import React, { useEffect, useState } from 'react';
import { Award, CheckCircle2 } from 'lucide-react';
import { Card, SectionHeading, LoadingState, Badge, Button } from '../components/ui';
import { getComparison } from '../api/simulationApi';
import { getMaterialById } from '../mock/materials';
import { ScenarioResult } from '../types';
import { ShelterVisualization, ShelterGeometry } from '../components/ShelterVisualization';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { useNavigate } from 'react-router-dom';

export default function Comparison() {
  const [scenarios, setScenarios] = useState<ScenarioResult[] | null>(null);
  const { draft, setDraft, project, setProject, simulation, setSimulation } = useAnalysis();
  const navigate = useNavigate();

  useEffect(() => {
    getComparison('demo').then(setScenarios);
  }, []);

  if (!scenarios) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Shelter Designs" description="Evaluate and select optimal shelter designs." />
        <Card><LoadingState message="Loading design candidates..." /></Card>
      </div>
    );
  }

  const handleSelectDesign = (scenario: ScenarioResult) => {
    setDraft((d) => ({ ...d, design: scenario.design }));
    if (project) {
      setProject({ ...project, design: scenario.design });
    }
    if (simulation) {
      setSimulation({
        ...simulation,
        id: `sim-${scenario.design.id}-${Date.now().toString().slice(-6)}`,
        status: 'Completed'
      });
    }
    navigate('/simulation');
  };

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

  return (
    <div className="space-y-6 pb-12">
      <SectionHeading 
        title="Shelter Designs" 
        description="Select from the generated AI engineering designs. Previews show actual 3D orientation and structural layout." 
      />

      <div className="grid lg:grid-cols-2 gap-6">
        {scenarios.map((s) => {
          const wall = getMaterialById(s.design.wallMaterialId);
          const insulation = getMaterialById(s.design.insulationMaterialId);
          const isSelected = draft.design.id === s.design.id || project?.design.id === s.design.id;
          
          return (
            <Card 
              key={s.designId} 
              className={`transition-all duration-300 relative overflow-hidden ${isSelected ? 'ring-2 ring-brand-500 shadow-md' : 'hover:border-brand-300'}`}
            >
              {s.isRecommended && (
                <div className="absolute top-0 right-0 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 uppercase tracking-wider rounded-bl-lg z-20 flex items-center gap-1">
                  <Award size={12} /> AI Recommended
                </div>
              )}
              {isSelected && (
                <div className="absolute top-0 left-0 bg-brand-500 text-white text-[10px] font-bold px-3 py-1 uppercase tracking-wider rounded-br-lg z-20 flex items-center gap-1">
                  <CheckCircle2 size={12} /> Selected
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-4 h-full">
                {/* 3D Preview (Left side) */}
                <div className="h-64 md:h-auto min-h-[250px] relative rounded-lg overflow-hidden bg-slate-950/80">
                  <ShelterVisualization 
                    geometry={mapDesignToGeometry(s.design)} 
                    isSimulating={false}
                  />
                </div>

                {/* Info (Right side) */}
                <div className="flex flex-col justify-between py-2">
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 mb-1 flex items-center gap-2">
                      {s.designLabel}
                    </h3>
                    
                    <div className="flex items-center gap-2 mb-4">
                      <Badge tone={s.overallScore > 80 ? 'green' : s.overallScore > 60 ? 'amber' : 'slate'}>
                        Suitability: {s.overallScore}%
                      </Badge>
                      <Badge tone="blue">{s.design.orientation}</Badge>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between border-b border-slate-100 pb-1">
                        <span className="text-slate-500">Dimensions</span>
                        <span className="font-medium text-slate-700">{s.design.length}m × {s.design.width}m</span>
                      </div>
                      <div className="flex justify-between border-b border-slate-100 pb-1">
                        <span className="text-slate-500">Wall System</span>
                        <span className="font-medium text-slate-700 truncate max-w-[140px]" title={wall?.name}>{wall?.name}</span>
                      </div>
                      <div className="flex justify-between border-b border-slate-100 pb-1">
                        <span className="text-slate-500">Insulation</span>
                        <span className="font-medium text-slate-700">{insulation?.name}</span>
                      </div>
                      <div className="flex justify-between border-b border-slate-100 pb-1">
                        <span className="text-slate-500">Comfort Band</span>
                        <span className="font-medium text-emerald-600">{s.comfortPercentage}% of year</span>
                      </div>
                      <div className="flex justify-between pb-1">
                        <span className="text-slate-500">Heat Loss</span>
                        <span className="font-medium text-red-500">{s.heatLoss} kWh</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <Button 
                      variant={isSelected ? 'secondary' : 'primary'} 
                      className="w-full"
                      onClick={() => handleSelectDesign(s)}
                    >
                      {isSelected ? 'Currently Selected' : 'Select Design'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
