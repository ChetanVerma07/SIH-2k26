import { AnalysisProject, ClimateData, ShelterRequirements, ShelterDesign, DesignMode } from '../types';
import { delay } from './client';

// POST /analyses
export async function createAnalysis(payload: {
  name: string;
  climate: ClimateData;
  requirements: ShelterRequirements;
  design: ShelterDesign;
  designMode: DesignMode;
}): Promise<AnalysisProject> {
  const project: AnalysisProject = {
    id: `analysis-${Date.now()}`,
    name: payload.name,
    createdAt: new Date().toISOString(),
    climate: payload.climate,
    requirements: payload.requirements,
    design: payload.design,
    designMode: payload.designMode,
    status: 'queued',
  };
  return delay(project, 250);
}

// GET /analyses/recent  (dashboard "recent analyses" widget)
export async function getRecentAnalyses(): Promise<
  Array<{ id: string; name: string; location: string; date: string; comfort: number; status: string }>
> {
  return delay([
    {
      id: 'a-1024',
      name: 'Leh Winter Shelter v3',
      location: 'Leh, Ladakh',
      date: '2026-09-10',
      comfort: 87,
      status: 'Completed',
    },
    {
      id: 'a-1023',
      name: 'Jaisalmer Desert Cabin',
      location: 'Jaisalmer, Rajasthan',
      date: '2026-09-08',
      comfort: 79,
      status: 'Completed',
    },
    {
      id: 'a-1022',
      name: 'Kochi Coastal Unit',
      location: 'Kochi, Kerala',
      date: '2026-09-05',
      comfort: 72,
      status: 'Completed',
    },
    {
      id: 'a-1021',
      name: 'Leh Winter Shelter v2',
      location: 'Leh, Ladakh',
      date: '2026-09-02',
      comfort: 81,
      status: 'Completed',
    },
  ]);
}
