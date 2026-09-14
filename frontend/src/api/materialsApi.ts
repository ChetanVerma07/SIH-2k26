import { Material, MaterialCategory } from '../types';
import { MATERIALS } from '../mock/materials';
import { apiGet, delay, USE_MOCK_API } from './client';

type BackendMaterial = {
  id: string;
  name: string;
  category: string;
  thermal_conductivity: number;
  density: number;
  specific_heat: number;
  cost_factor: number;
};

function adaptMaterial(material: BackendMaterial): Material {
  return {
    id: material.id,
    name: material.name,
    category: (material.category.charAt(0).toUpperCase() + material.category.slice(1)) as MaterialCategory,
    thermalConductivity: material.thermal_conductivity,
    density: material.density,
    specificHeat: material.specific_heat,
    costFactor: material.cost_factor,
    description: 'Material supplied by the integrated backend library.',
  };
}

// GET /materials?category=
export async function getMaterials(category?: MaterialCategory): Promise<Material[]> {
  if (USE_MOCK_API) {
    const list = category ? MATERIALS.filter((m) => m.category === category) : MATERIALS;
    return delay(list);
  }

  const query = category ? `?category=${encodeURIComponent(category.toLowerCase())}` : '';
  const response = await apiGet<BackendMaterial[]>(`/materials${query}`);
  return response.map(adaptMaterial);
}

// GET /materials/:id
export async function getMaterialById(id: string): Promise<Material | undefined> {
  if (USE_MOCK_API) return delay(MATERIALS.find((m) => m.id === id));

  return adaptMaterial(await apiGet<BackendMaterial>(`/materials/${encodeURIComponent(id)}`));
}
