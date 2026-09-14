import React, { useEffect, useMemo, useState } from 'react';
import { Search, X } from 'lucide-react';
import { Card, SectionHeading, TextInput, Select, Badge, EmptyState } from '../components/ui';
import { getMaterials } from '../api/materialsApi';
import { Material, MaterialCategory } from '../types';

const CATEGORIES: (MaterialCategory | 'All')[] = ['All', 'Wall', 'Roof', 'Floor', 'Insulation'];

export default function Materials() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<MaterialCategory | 'All'>('All');
  const [selected, setSelected] = useState<Material | null>(null);

  useEffect(() => {
    getMaterials().then(setMaterials);
  }, []);

  const filtered = useMemo(() => {
    return materials.filter((m) => {
      const matchesCategory = category === 'All' || m.category === category;
      const matchesQuery = m.name.toLowerCase().includes(query.toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [materials, query, category]);

  return (
    <div className="space-y-6">
      <SectionHeading title="Materials" description="Browse the material library used for wall, roof, floor, and insulation layers." />

      <Card>
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <TextInput
              placeholder="Search materials..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9 w-full"
              aria-label="Search materials"
            />
          </div>
          <Select value={category} onChange={(e) => setCategory(e.target.value as any)} aria-label="Filter by category">
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </Select>
        </div>

        {filtered.length === 0 ? (
          <EmptyState title="No materials found" message="Try adjusting your search or category filter." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-100">
                  <th className="py-2 pr-4 font-medium">Material</th>
                  <th className="py-2 pr-4 font-medium">Category</th>
                  <th className="py-2 pr-4 font-medium">Thermal Conductivity (W/mK)</th>
                  <th className="py-2 pr-4 font-medium">Density (kg/m³)</th>
                  <th className="py-2 pr-4 font-medium">Specific Heat (J/kgK)</th>
                  <th className="py-2 font-medium">Cost Factor</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((m) => (
                  <tr
                    key={m.id}
                    className="border-b border-slate-50 last:border-0 hover:bg-slate-50 cursor-pointer"
                    onClick={() => setSelected(m)}
                  >
                    <td className="py-2.5 pr-4 font-medium text-slate-800">{m.name}</td>
                    <td className="py-2.5 pr-4"><Badge tone="blue">{m.category}</Badge></td>
                    <td className="py-2.5 pr-4 text-slate-600">{m.thermalConductivity}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{m.density}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{m.specificHeat}</td>
                    <td className="py-2.5 text-slate-600">{m.costFactor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-40 p-4" onClick={() => setSelected(null)}>
          <div
            className="bg-white rounded-lg shadow-lg max-w-md w-full p-6"
            role="dialog"
            aria-modal="true"
            aria-labelledby="material-detail-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 id="material-detail-title" className="text-lg font-semibold text-slate-900">{selected.name}</h3>
              <button onClick={() => setSelected(null)} aria-label="Close details" className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>
            <Badge tone="blue">{selected.category}</Badge>
            <p className="text-sm text-slate-600 mt-3">{selected.description}</p>
            <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
              <div><p className="text-slate-500 text-xs">Thermal Conductivity</p><p className="font-medium">{selected.thermalConductivity} W/mK</p></div>
              <div><p className="text-slate-500 text-xs">Density</p><p className="font-medium">{selected.density} kg/m³</p></div>
              <div><p className="text-slate-500 text-xs">Specific Heat</p><p className="font-medium">{selected.specificHeat} J/kgK</p></div>
              <div><p className="text-slate-500 text-xs">Cost Factor</p><p className="font-medium">{selected.costFactor}</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
