import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  AnalysisProject,
  ClimateData,
  ShelterRequirements,
  ShelterDesign,
  DesignMode,
  Simulation,
} from '../types';
import { LADAKH_CLIMATE } from '../mock/climate';
import { BASELINE_DESIGN } from '../mock/designs';

const STORAGE_KEY = 'phase9.currentAnalysis';

export interface DraftAnalysis {
  name: string;
  climate: ClimateData;
  requirements: ShelterRequirements;
  design: ShelterDesign;
  designMode: DesignMode;
}

interface AnalysisContextValue {
  draft: DraftAnalysis;
  setDraft: React.Dispatch<React.SetStateAction<DraftAnalysis>>;
  project: AnalysisProject | null;
  setProject: (p: AnalysisProject | null) => void;
  simulation: Simulation | null;
  setSimulation: (s: Simulation | null) => void;
  resetDraft: () => void;
}

const defaultDraft: DraftAnalysis = {
  name: 'Leh Winter Shelter v3',
  climate: LADAKH_CLIMATE,
  requirements: {
    targetIndoorTempMin: 16,
    targetIndoorTempMax: 22,
    occupants: 4,
    floorArea: 24,
    budget: 450000,
    simulationDurationHours: 24,
  },
  design: BASELINE_DESIGN,
  designMode: 'AUTO_OPTIMIZE',
};

const AnalysisContext = createContext<AnalysisContextValue | undefined>(undefined);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<DraftAnalysis>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? { ...defaultDraft, ...JSON.parse(raw) } : defaultDraft;
    } catch {
      return defaultDraft;
    }
  });
  const [project, setProject] = useState<AnalysisProject | null>(null);
  const [simulation, setSimulation] = useState<Simulation | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
    } catch {
      /* ignore quota errors in demo */
    }
  }, [draft]);

  const resetDraft = () => setDraft(defaultDraft);

  return (
    <AnalysisContext.Provider
      value={{ draft, setDraft, project, setProject, simulation, setSimulation, resetDraft }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis must be used within AnalysisProvider');
  return ctx;
}
