import { AnalysisProject, ClimateData, ShelterRequirements, ShelterDesign, DesignMode } from '../types';
import { apiGet, apiPost, delay, USE_MOCK_API } from './client';
import { MATERIALS } from '../mock/materials';

type BackendProject = { id: string; name: string; location: string; created_at: string };
type BackendClimate = { id: string; location?: string };
type BackendMaterial = { id: string; name: string; category: string };

const ORIENTATION_MAP: Record<string, string> = {
  North: 'N',
  'North-East': 'NE',
  East: 'E',
  'South-East': 'SE',
  South: 'S',
  'South-West': 'SW',
  West: 'W',
  'North-West': 'NW',
};

export const analysisRuntime = new Map<string, { projectId: string; designId: string; climateId: string }>();

// POST /analyses
export async function createAnalysis(payload: {
  name: string;
  climate: ClimateData;
  requirements: ShelterRequirements;
  design: ShelterDesign;
  designMode: DesignMode;
}): Promise<AnalysisProject> {
  if (USE_MOCK_API) {
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

  const project = await apiPost<BackendProject>('/projects', {
    name: payload.name,
    location: payload.climate.locationName,
    description: `Created from the ${payload.designMode.toLowerCase()} design workflow.`,
  });
  const climatePresets = await apiGet<BackendClimate[]>('/climate/presets');
  const climate = climatePresets.find((item) =>
    (item.location || '').toLowerCase() === payload.climate.locationName.toLowerCase()
    || (item.location || '').toLowerCase().includes(payload.climate.locationName.split(',')[0].toLowerCase())
  ) || climatePresets[0];
  const backendMaterials = await apiGet<BackendMaterial[]>('/materials');
  const findMaterial = (frontendId: string) => {
    const frontend = MATERIALS.find((item) => item.id === frontendId);
    return backendMaterials.find((item) => item.name.toLowerCase() === frontend?.name.toLowerCase())?.id
      || backendMaterials.find((item) => item.category === frontend?.category.toLowerCase())?.id
      || backendMaterials[0]?.id;
  };
  const design = await apiPost<{ id: string }>('/designs', {
    project_id: project.id,
    length: payload.design.length,
    width: payload.design.width,
    height: payload.design.height,
    wall_thickness: payload.design.wallThickness,
    roof_thickness: payload.design.roofThickness,
    floor_thickness: payload.design.floorThickness,
    insulation_thickness: payload.design.insulationThickness,
    opening_percentage: payload.design.openingPercentage,
    orientation: ORIENTATION_MAP[payload.design.orientation] || 'S',
    wall_material: findMaterial(payload.design.wallMaterialId),
    roof_material: findMaterial(payload.design.roofMaterialId),
    floor_material: findMaterial(payload.design.floorMaterialId),
    insulation_material: findMaterial(payload.design.insulationMaterialId),
    occupants: payload.requirements.occupants,
    floor_area: payload.requirements.floorArea,
    target_min_temperature: payload.requirements.targetIndoorTempMin,
    target_max_temperature: payload.requirements.targetIndoorTempMax,
  });
  analysisRuntime.set(project.id, {
    projectId: project.id,
    designId: design.id,
    climateId: climate.id,
  });
  return {
    id: project.id,
    name: project.name,
    createdAt: project.created_at,
    climate: payload.climate,
    requirements: payload.requirements,
    design: { ...payload.design, id: design.id },
    designMode: payload.designMode,
    status: 'queued',
  };
}

// GET /analyses/recent  (dashboard "recent analyses" widget)
export async function getRecentAnalyses(): Promise<
  Array<{ id: string; name: string; location: string; date: string; comfort: number; status: string }>
> {
  if (USE_MOCK_API) {
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

  const projects = await apiGet<BackendProject[]>('/projects');
  return projects.map((project) => ({
    id: project.id,
    name: project.name,
    location: project.location,
    date: new Date(project.created_at).toISOString().slice(0, 10),
    comfort: 0,
    status: 'Created',
  }));
}
