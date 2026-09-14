import { Material, MaterialCategory } from '../types';
import { MATERIALS } from '../mock/materials';
import { delay } from './client';

// GET /materials?category=
export async function getMaterials(category?: MaterialCategory): Promise<Material[]> {
  const list = category ? MATERIALS.filter((m) => m.category === category) : MATERIALS;
  return delay(list);
}

// GET /materials/:id
export async function getMaterialById(id: string): Promise<Material | undefined> {
  return delay(MATERIALS.find((m) => m.id === id));
}
