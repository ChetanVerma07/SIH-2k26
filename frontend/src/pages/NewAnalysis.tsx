import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Info } from 'lucide-react';
import {
  Card,
  Field,
  TextInput,
  Select,
  Button,
  SectionHeading,
  Badge,
  Tooltip,
} from '../components/ui';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { CLIMATE_PRESETS } from '../mock/climate';
import { MATERIALS, getMaterialById } from '../mock/materials';
import { createAnalysis } from '../api/analysisApi';
import { runSimulation } from '../api/simulationApi';
import { DesignMode } from '../types';
import { ShelterVisualization } from '../components/ShelterVisualization';
import { SliderField } from '../components/ui';

const ORIENTATIONS = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West'];

export default function NewAnalysis() {
  const navigate = useNavigate();
  const { draft, setDraft, setProject, setSimulation, resetDraft } = useAnalysis();
  const [presetId, setPresetId] = useState('ladakh');
  const [climateMode, setClimateMode] = useState<'manual' | 'dataset'>('dataset');
  const [errors, setErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const preset = CLIMATE_PRESETS.find((p) => p.id === presetId);
    if (preset && climateMode === 'dataset') {
      setDraft((d) => ({ ...d, climate: preset.climate }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presetId, climateMode]);

  const wallMaterials = MATERIALS.filter((m) => m.category === 'Wall');
  const roofMaterials = MATERIALS.filter((m) => m.category === 'Roof');
  const floorMaterials = MATERIALS.filter((m) => m.category === 'Floor');
  const insulationMaterials = MATERIALS.filter((m) => m.category === 'Insulation');

  function validate(): string[] {
    const errs: string[] = [];
    if (!draft.name.trim()) errs.push('Analysis name is required.');
    if (draft.requirements.targetIndoorTempMin >= draft.requirements.targetIndoorTempMax)
      errs.push('Minimum indoor temperature must be less than maximum.');
    if (draft.requirements.occupants <= 0) errs.push('Number of occupants must be greater than zero.');
    if (draft.requirements.floorArea <= 0) errs.push('Required floor area must be greater than zero.');
    if (draft.design.length <= 0 || draft.design.width <= 0 || draft.design.height <= 0)
      errs.push('Length, width, and height must all be greater than zero.');
    if (draft.design.openingPercentage < 0 || draft.design.openingPercentage > 90)
      errs.push('Opening percentage must be between 0 and 90.');
    return errs;
  }

  async function handleSubmit() {
    const errs = validate();
    setErrors(errs);
    if (errs.length > 0) return;
    setSubmitting(true);
    const project = await createAnalysis({
      name: draft.name,
      climate: draft.climate,
      requirements: draft.requirements,
      design: draft.design,
      designMode: draft.designMode,
    });
    setProject(project);
    const sim = await runSimulation(project.id);
    setSimulation(sim);
    setSubmitting(false);
    navigate('/simulation');
  }

  return (
    <div className="space-y-6">
      <SectionHeading
        title="New Analysis"
        description="Configure location, climate, requirements, design and materials, then run the analysis."
      />

      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-md p-4 text-sm" role="alert">
          <p className="font-medium mb-1">Please fix the following before continuing:</p>
          <ul className="list-disc list-inside space-y-0.5">
            {errors.map((e) => <li key={e}>{e}</li>)}
          </ul>
        </div>
      )}

      <Card title="Analysis Name">
        <Field label="Analysis name" htmlFor="analysis-name">
          <TextInput
            id="analysis-name"
            value={draft.name}
            onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
          />
        </Field>
      </Card>

      {/* Section A: Location */}
      <Card title="A. Location" subtitle="Select a preset location/climate or define your own.">
        <div className="grid md:grid-cols-2 gap-4">
          <Field label="Location Preset" htmlFor="preset">
            <Select id="preset" value={presetId} onChange={(e) => setPresetId(e.target.value)}>
              {CLIMATE_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </Select>
          </Field>
          <Field label="Location Name" htmlFor="loc-name">
            <TextInput
              id="loc-name"
              value={draft.climate.locationName}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, locationName: e.target.value } }))}
            />
          </Field>
          <Field label="Latitude" htmlFor="lat">
            <TextInput
              id="lat"
              type="number"
              value={draft.climate.latitude}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, latitude: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Longitude" htmlFor="lng">
            <TextInput
              id="lng"
              type="number"
              value={draft.climate.longitude}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, longitude: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Climate Type" htmlFor="climate-type">
            <Select
              id="climate-type"
              value={draft.climate.climateType}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, climateType: e.target.value as any } }))}
            >
              {['High Altitude Cold', 'Hot & Dry', 'Warm & Humid', 'Composite', 'User Defined'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      {/* Section B: Climate */}
      <Card title="B. Climate" subtitle="Use the selected dataset or manually override climate parameters.">
        <div className="flex gap-2 mb-4">
          <Button
            variant={climateMode === 'dataset' ? 'primary' : 'secondary'}
            onClick={() => setClimateMode('dataset')}
            type="button"
          >
            Use Climate Dataset
          </Button>
          <Button
            variant={climateMode === 'manual' ? 'primary' : 'secondary'}
            onClick={() => setClimateMode('manual')}
            type="button"
          >
            Manual Input
          </Button>
        </div>
        <fieldset disabled={climateMode === 'dataset'} className="grid md:grid-cols-3 gap-4 disabled:opacity-60">
          <Field label="Ambient Temperature (°C)" htmlFor="amb-temp">
            <TextInput
              id="amb-temp"
              type="number"
              value={draft.climate.ambientTemperature}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, ambientTemperature: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Relative Humidity (%)" htmlFor="rh">
            <TextInput
              id="rh"
              type="number"
              value={draft.climate.relativeHumidity}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, relativeHumidity: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Atmospheric Pressure (kPa)" htmlFor="pressure">
            <TextInput
              id="pressure"
              type="number"
              value={draft.climate.atmosphericPressure}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, atmosphericPressure: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Solar Radiation (W/m²)" htmlFor="solar">
            <TextInput
              id="solar"
              type="number"
              value={draft.climate.solarRadiation}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, solarRadiation: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Wind Speed (m/s)" htmlFor="wind">
            <TextInput
              id="wind"
              type="number"
              value={draft.climate.windSpeed}
              onChange={(e) => setDraft((d) => ({ ...d, climate: { ...d.climate, windSpeed: Number(e.target.value) } }))}
            />
          </Field>
        </fieldset>
      </Card>

      {/* Section C: Shelter Requirements */}
      <Card title="C. Shelter Requirements">
        <div className="grid md:grid-cols-3 gap-4">
          <Field label="Target Indoor Temp — Min (°C)" htmlFor="ti-min">
            <TextInput
              id="ti-min"
              type="number"
              value={draft.requirements.targetIndoorTempMin}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, targetIndoorTempMin: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Target Indoor Temp — Max (°C)" htmlFor="ti-max">
            <TextInput
              id="ti-max"
              type="number"
              value={draft.requirements.targetIndoorTempMax}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, targetIndoorTempMax: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Number of Occupants" htmlFor="occupants">
            <TextInput
              id="occupants"
              type="number"
              value={draft.requirements.occupants}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, occupants: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Required Floor Area (m²)" htmlFor="floor-area">
            <TextInput
              id="floor-area"
              type="number"
              value={draft.requirements.floorArea}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, floorArea: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Budget (INR)" htmlFor="budget">
            <TextInput
              id="budget"
              type="number"
              value={draft.requirements.budget}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, budget: Number(e.target.value) } }))}
            />
          </Field>
          <Field label="Simulation Duration (hours)" htmlFor="sim-duration">
            <TextInput
              id="sim-duration"
              type="number"
              value={draft.requirements.simulationDurationHours}
              onChange={(e) => setDraft((d) => ({ ...d, requirements: { ...d.requirements, simulationDurationHours: Number(e.target.value) } }))}
            />
          </Field>
        </div>
      </Card>

      {/* Section D: Design Parameters */}
      <Card title="D. Design Parameters">
        <div className="flex gap-2 mb-6">
          {(['AUTO_OPTIMIZE', 'MANUAL'] as DesignMode[]).map((mode) => (
            <Button
              key={mode}
              variant={draft.designMode === mode ? 'primary' : 'secondary'}
              type="button"
              onClick={() => setDraft((d) => ({ ...d, designMode: mode }))}
            >
              {mode === 'AUTO_OPTIMIZE' ? 'Auto Optimize' : 'Manual Design'}
            </Button>
          ))}
          <Tooltip text="Auto Optimize lets the optimizer search dimensions and materials automatically.">
            <Info size={16} className="text-slate-400 self-center" />
          </Tooltip>
        </div>
        
        <div className="grid lg:grid-cols-3 gap-8">
          <fieldset disabled={draft.designMode === 'AUTO_OPTIMIZE'} className="lg:col-span-2 grid md:grid-cols-2 gap-x-6 gap-y-4 disabled:opacity-60">
            <SliderField label="Length" unit="m" min={1} max={15} step={0.1} value={draft.design.length} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, length: v } }))} />
            <SliderField label="Width" unit="m" min={1} max={15} step={0.1} value={draft.design.width} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, width: v } }))} />
            <SliderField label="Height" unit="m" min={1.5} max={5} step={0.1} value={draft.design.height} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, height: v } }))} />
            
            <SliderField label="Wall Thickness" unit="m" min={0.05} max={0.6} step={0.01} value={draft.design.wallThickness} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, wallThickness: v } }))} />
            <SliderField label="Roof Thickness" unit="m" min={0.05} max={0.6} step={0.01} value={draft.design.roofThickness} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, roofThickness: v } }))} />
            <SliderField label="Floor Thickness" unit="m" min={0.05} max={0.6} step={0.01} value={draft.design.floorThickness} onChange={(v) => setDraft((d) => ({ ...d, design: { ...d.design, floorThickness: v } }))} />
          <Field label="Insulation Thickness (m)" htmlFor="insul-thick">
            <TextInput id="insul-thick" type="number" step="0.01" value={draft.design.insulationThickness} onChange={(e) => setDraft((d) => ({ ...d, design: { ...d.design, insulationThickness: Number(e.target.value) } }))} />
          </Field>
          <Field label="Opening Percentage (%)" htmlFor="opening-pct">
            <TextInput id="opening-pct" type="number" value={draft.design.openingPercentage} onChange={(e) => setDraft((d) => ({ ...d, design: { ...d.design, openingPercentage: Number(e.target.value) } }))} />
          </Field>
          <Field label="Orientation" htmlFor="orientation">
            <Select id="orientation" value={draft.design.orientation} onChange={(e) => setDraft((d) => ({ ...d, design: { ...d.design, orientation: e.target.value } }))}>
              {ORIENTATIONS.map((o) => <option key={o} value={o}>{o}</option>)}
            </Select>
          </Field>
          </fieldset>
          
          <div className="flex justify-center items-center p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <ShelterVisualization 
              geometry={{
                lengthM: draft.design.length || 1,
                widthM: draft.design.width || 1,
                heightM: draft.design.height || 1,
                wallThicknessM: draft.design.wallThickness,
                roofType: 'flat',
                orientation: draft.design.orientation.charAt(0),
                windowAreaM2: (draft.design.length * draft.design.height * draft.design.openingPercentage) / 100,
                doorAreaM2: 2,
              }} 
            />
          </div>
        </div>
      </Card>

      {/* Section E: Materials */}
      <Card title="E. Materials" subtitle="Select materials for each shelter component.">
        <fieldset disabled={draft.designMode === 'AUTO_OPTIMIZE'} className="grid md:grid-cols-2 gap-6 disabled:opacity-60">
          {[
            { key: 'wallMaterialId' as const, label: 'Wall Material', options: wallMaterials },
            { key: 'roofMaterialId' as const, label: 'Roof Material', options: roofMaterials },
            { key: 'floorMaterialId' as const, label: 'Floor Material', options: floorMaterials },
            { key: 'insulationMaterialId' as const, label: 'Insulation Material', options: insulationMaterials },
          ].map(({ key, label, options }) => {
            const selected = getMaterialById(draft.design[key]);
            return (
              <div key={key} className="space-y-2">
                <Field label={label} htmlFor={key}>
                  <Select
                    id={key}
                    value={draft.design[key]}
                    onChange={(e) => setDraft((d) => ({ ...d, design: { ...d.design, [key]: e.target.value } }))}
                  >
                    {options.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </Select>
                </Field>
                {selected && (
                  <div className="text-xs text-slate-500 bg-slate-50 border border-slate-100 rounded-md p-2 flex flex-wrap gap-x-4 gap-y-1">
                    <span>k: {selected.thermalConductivity} W/mK</span>
                    <span>ρ: {selected.density} kg/m³</span>
                    <span>Cp: {selected.specificHeat} J/kgK</span>
                    <span>Cost index: {selected.costFactor}</span>
                  </div>
                )}
              </div>
            );
          })}
        </fieldset>
        {draft.designMode === 'AUTO_OPTIMIZE' && (
          <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
            <Badge tone="blue">Auto Optimize</Badge> Materials and design parameters will be selected automatically by the optimizer.
          </p>
        )}
      </Card>

      {/* Section F: Action */}
      <div className="flex gap-3 pb-6">
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? 'Starting Analysis...' : 'Run Analysis'}
        </Button>
        <Button variant="secondary" type="button" onClick={resetDraft}>
          Reset
        </Button>
      </div>
    </div>
  );
}
