import React, { useMemo, useState } from 'react';
import { Viewer, Entity, PolygonGraphics, PointGraphics, LabelGraphics, CameraFlyTo, PolylineGraphics, EllipseGraphics } from 'resium';
import { Ion, Cartesian3, Color, Terrain } from 'cesium';
import { ArrowRight, Activity, ThermometerSun, Wind, Mountain, Navigation2 } from 'lucide-react';
import { Card, SectionHeading, Badge, Button } from '../components/ui';
import { MOCK_LADAKH_BOUNDARY, MOCK_TERRAIN_SITES, MOCK_THERMAL_ZONES, LADAKH_CENTER, TerrainSite } from '../mock/terrainMock';
import { useAnalysis } from '../hooks/useAnalysisContext';
import { useNavigate } from 'react-router-dom';

const CESIUM_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;

if (CESIUM_TOKEN) {
  Ion.defaultAccessToken = CESIUM_TOKEN;
}

const MOCK_THERMAL_COLD = Cartesian3.fromDegreesArray(MOCK_THERMAL_ZONES.cold);
const MOCK_THERMAL_MODERATE = Cartesian3.fromDegreesArray(MOCK_THERMAL_ZONES.moderate);
const MOCK_THERMAL_WARM = Cartesian3.fromDegreesArray(MOCK_THERMAL_ZONES.warm);
const LADAKH_BOUNDARY = Cartesian3.fromDegreesArray(MOCK_LADAKH_BOUNDARY);

export default function TerrainIntelligence() {
  const [selectedSite, setSelectedSite] = useState<TerrainSite | null>(
    MOCK_TERRAIN_SITES.find(s => s.isRecommended) || null
  );
  const worldTerrain = useMemo(
    () => Terrain.fromWorldTerrain({ requestVertexNormals: true }),
    []
  );
  
  const { setDraft } = useAnalysis();
  const navigate = useNavigate();

  const handleAnalyzeHere = () => {
    if (!selectedSite) return;
    setDraft(d => ({
      ...d,
      climate: {
        ...d.climate,
        locationName: selectedSite.name,
        latitude: selectedSite.lat,
        longitude: selectedSite.lng,
      }
    }));
    navigate('/new-analysis');
  };

  if (!CESIUM_TOKEN) {
    return (
      <div className="space-y-6">
        <SectionHeading title="3D Terrain Map" description="3D site analysis and AI recommendations for Ladakh." />
        <Card>
          <div className="p-8 text-center text-slate-500">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Cesium Token Required</h3>
            <p>Please add <code>VITE_CESIUM_ION_TOKEN=your_token_here</code> to your <code>.env</code> file to enable the 3D globe.</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
      <SectionHeading 
        title="LADAKH — 3D TERRAIN INTELLIGENCE" 
        description="Interactive Google-Earth style 3D terrain viewer powered by CesiumJS." 
      />

      <div className="grid lg:grid-cols-3 gap-6 flex-1 min-h-[600px]">
        {/* 3D CESIUM GLOBE */}
        <div className="lg:col-span-2 relative rounded-lg overflow-hidden border border-slate-200 shadow-sm bg-slate-900 group">
          <div className="absolute top-4 left-4 z-10 pointer-events-none">
            <Badge tone="amber">SIMULATED THERMAL DATA</Badge>
          </div>
          
          <Viewer 
            full 
            timeline={false} 
            animation={false} 
            sceneModePicker={false} 
            baseLayerPicker={false}
            geocoder={false}
            homeButton={false}
            navigationHelpButton={false}
            infoBox={false}
            showRenderLoopErrors
            terrain={worldTerrain}
          >
            {/* Fly to Ladakh on load */}
            <CameraFlyTo 
              duration={0} 
              destination={Cartesian3.fromDegrees(LADAKH_CENTER.lng, LADAKH_CENTER.lat - 0.05, 5000)}
              orientation={{
                heading: 0.0,
                pitch: -0.5,
                roll: 0.0,
              }}
            />

            {/* Analysis Boundary */}
            <Entity>
              <PolylineGraphics
                positions={LADAKH_BOUNDARY}
                width={3}
                material={Color.GOLD.withAlpha(0.8)}
              />
            </Entity>

            {/* Simulated Thermal Overlay */}
            <Entity>
              <PolygonGraphics hierarchy={MOCK_THERMAL_COLD as any} material={Color.BLUE.withAlpha(0.2)} />
            </Entity>
            <Entity>
              <PolygonGraphics hierarchy={MOCK_THERMAL_MODERATE as any} material={Color.YELLOW.withAlpha(0.2)} />
            </Entity>
            <Entity>
              <PolygonGraphics hierarchy={MOCK_THERMAL_WARM as any} material={Color.RED.withAlpha(0.2)} />
            </Entity>

            {/* Candidate Sites */}
            {MOCK_TERRAIN_SITES.map((site) => {
              const isSelected = selectedSite?.id === site.id;
              const position = Cartesian3.fromDegrees(site.lng, site.lat, site.elevation);
              const color = site.isRecommended ? Color.fromCssColorString('#10b981') : Color.fromCssColorString('#3b82f6');
              const labelText = site.isRecommended ? '★ AI RECOMMENDED SITE ★' : 'CANDIDATE SITE';
              const arrowText = isSelected ? `Orientation: ${site.recommendedOrientation}` : '';

              return (
                <Entity 
                  key={site.id} 
                  position={position} 
                  name={site.name}
                  onClick={() => setSelectedSite(site)}
                >
                  <PointGraphics 
                    color={color} 
                    pixelSize={isSelected ? 16 : 10} 
                    outlineColor={Color.WHITE} 
                    outlineWidth={2} 
                  />
                  <LabelGraphics 
                    text={isSelected ? `${labelText}\n${arrowText}` : labelText} 
                    font="14pt monospace" 
                    fillColor={Color.WHITE}
                    showBackground={true}
                    backgroundColor={Color.BLACK.withAlpha(0.7)}
                    pixelOffset={new Cartesian3(0, -30, 0) as any}
                  />
                  {isSelected && (
                    <>
                      <EllipseGraphics semiMajorAxis={650} semiMinorAxis={650} material={Color.CYAN.withAlpha(0.12)} outline outlineColor={Color.CYAN} outlineWidth={2} />
                      <PolylineGraphics positions={Cartesian3.fromDegreesArrayHeights([site.lng, site.lat, site.elevation, site.lng + 0.008, site.lat + 0.002, site.elevation + 80])} width={5} material={Color.CYAN} />
                    </>
                  )}
                </Entity>
              );
            })}
          </Viewer>

          {/* Map HUD Legend */}
          <div className="absolute bottom-4 left-4 z-10 bg-slate-900/80 backdrop-blur-md p-3 rounded-md border border-slate-700 pointer-events-none shadow-xl">
            <h4 className="text-[10px] font-mono text-slate-300 uppercase tracking-wider mb-2">Simulated Data Layers</h4>
            <div className="flex items-center gap-4 text-xs font-medium text-white mb-2">
              <div className="flex items-center gap-1.5"><ThermometerSun size={14} className="text-amber-500" /> Thermal Overlays</div>
              <div className="flex items-center gap-1.5"><Mountain size={14} className="text-stone-400" /> Elevation DEM</div>
            </div>
            <div className="w-full h-1.5 rounded bg-gradient-to-r from-[#313695] via-[#ffffbf] to-[#d73027]"></div>
            <div className="flex justify-between text-[9px] text-slate-400 font-mono mt-1">
              <span>Cold</span>
              <span>Moderate</span>
              <span>Warm</span>
            </div>
          </div>
        </div>

        {/* AI SITE ANALYSIS PANEL */}
        <div className="h-full flex flex-col overflow-y-auto">
          {selectedSite ? (
            <Card className="flex-1 flex flex-col shadow-lg border-brand-100 relative overflow-hidden">
              {selectedSite.isRecommended && (
                <div className="absolute top-0 inset-x-0 h-1 bg-emerald-500" />
              )}
              <div className="flex items-start justify-between border-b border-slate-100 pb-4 mb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">AI Site Recommendation</h3>
                  <p className="text-lg font-semibold text-brand-700">{selectedSite.name}</p>
                  <p className="text-xs text-slate-500 font-mono mt-1">Lat: {selectedSite.lat.toFixed(4)} | Lng: {selectedSite.lng.toFixed(4)} | Elev: {selectedSite.elevation}m</p>
                </div>
                {selectedSite.isRecommended ? (
                  <Badge tone="green">Suitability: {selectedSite.suitabilityScore}%</Badge>
                ) : (
                  <Badge tone="slate">Score: {selectedSite.suitabilityScore}%</Badge>
                )}
              </div>

              <div className="space-y-4 flex-1">
                <p className="text-sm text-slate-700 leading-relaxed italic border-l-2 border-brand-200 pl-3">
                  "{selectedSite.description}"
                </p>

                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="bg-slate-50 p-3 rounded border border-slate-100 hover:border-slate-200 transition-colors">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase mb-1">
                      <ThermometerSun size={14} /> Solar Exposure
                    </div>
                    <div className={`font-bold ${selectedSite.solarExposure === 'High' ? 'text-amber-600' : 'text-slate-700'}`}>
                      {selectedSite.solarExposure}
                    </div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded border border-slate-100 hover:border-slate-200 transition-colors">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase mb-1">
                      <Mountain size={14} /> Terrain
                    </div>
                    <div className={`font-bold ${selectedSite.terrainSuitability === 'Excellent' ? 'text-emerald-600' : 'text-slate-700'}`}>
                      {selectedSite.terrainSuitability}
                    </div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded border border-slate-100 hover:border-slate-200 transition-colors">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase mb-1">
                      <Activity size={14} /> Thermal Potential
                    </div>
                    <div className={`font-bold ${selectedSite.thermalPotential === 'High' ? 'text-brand-600' : 'text-slate-700'}`}>
                      {selectedSite.thermalPotential}
                    </div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded border border-slate-100 hover:border-slate-200 transition-colors">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase mb-1">
                      <Wind size={14} /> Wind Exposure
                    </div>
                    <div className={`font-bold ${selectedSite.windExposure === 'High' ? 'text-red-500' : 'text-slate-700'}`}>
                      {selectedSite.windExposure}
                    </div>
                  </div>
                </div>

                <div className="bg-brand-50 p-4 rounded-md border border-brand-100 mt-4 shadow-inner">
                  <h4 className="text-xs font-bold text-brand-800 uppercase mb-3 flex items-center gap-2">
                    <ArrowRight size={14} /> AI Recommended Layout
                  </h4>
                  <ul className="text-sm text-brand-700 space-y-2 font-medium">
                    <li className="flex justify-between border-b border-brand-200/50 pb-1">
                      <span>Dimensions</span> <span>4.1m × 5.8m</span>
                    </li>
                    <li className="flex justify-between border-b border-brand-200/50 pb-1">
                      <span>Orientation</span> <span>{selectedSite.recommendedOrientation}</span>
                    </li>
                    <li className="flex justify-between">
                      <span>Foundation</span> <span>Stepped retaining</span>
                    </li>
                  </ul>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 mt-4">
                <Button className="w-full py-4 text-base shadow-md hover:shadow-lg flex items-center justify-center gap-2 font-bold" onClick={handleAnalyzeHere}>
                  Analyze Shelter Here <ArrowRight size={20} />
                </Button>
              </div>
            </Card>
          ) : (
            <Card className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-slate-50 border-dashed">
              <Mountain size={48} className="text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-700 mb-2">Select a Location</h3>
              <p className="text-slate-500">Click on any candidate site marker on the 3D globe to view its detailed AI analysis and environmental metrics.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
