import { useState, useMemo } from 'react'
import { RotateCw, ZoomIn, ZoomOut } from 'lucide-react'

export interface ShelterGeometry {
  lengthM: number
  widthM: number
  heightM: number
  wallThicknessM: number
  roofType: 'flat' | 'pitched' | 'vaulted'
  orientation: string
  windowAreaM2: number
  doorAreaM2: number
}

interface ShelterVisualizationProps {
  geometry: ShelterGeometry
  isSimulating?: boolean
}

const ORIENTATION_ROTATION: Record<string, number> = { N: 0, NE: 45, E: 90, SE: 135, S: 180, SW: 225, W: 270, NW: 315 }

export function ShelterVisualization({ geometry, isSimulating }: ShelterVisualizationProps) {
  const [userRotation, setUserRotation] = useState(0)
  const [zoom, setZoom] = useState(1)

  const baseRotation = ORIENTATION_ROTATION[geometry.orientation] ?? 180
  const rotation = baseRotation + userRotation

  // Math setup
  const maxDim = Math.max(geometry.lengthM, geometry.widthM, 3)
  const scale = 140 / maxDim
  const l = geometry.lengthM * scale
  const w = geometry.widthM * scale
  const h = geometry.heightM * scale

  // Roof math
  const rh = w * 0.35 // roof height
  const w_half = w / 2
  const roofSideLength = Math.sqrt(rh * rh + w_half * w_half)
  const roofAngleDeg = Math.atan2(rh, w_half) * (180 / Math.PI)

  const wireframeBase = "absolute top-1/2 left-1/2 border border-cyan-400/60 bg-cyan-950/20 shadow-[0_0_8px_rgba(34,211,238,0.2)_inset,0_0_5px_rgba(34,211,238,0.3)] backdrop-blur-[1px]"
  const glowPulse = isSimulating ? "animate-pulse" : ""

  const GridLines = () => (
    <div className="absolute inset-0 flex flex-col justify-evenly items-center opacity-30 pointer-events-none">
      <div className="w-full h-px bg-cyan-400/50"></div>
      <div className="w-full h-px bg-cyan-400/50"></div>
      <div className="absolute inset-0 flex justify-evenly items-center">
        <div className="w-px h-full bg-cyan-400/50"></div>
        <div className="w-px h-full bg-cyan-400/50"></div>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col items-center w-full h-full relative overflow-hidden group min-h-[400px] bg-slate-950/50 rounded-lg">
      {/* 3D Canvas */}
      <div
        className="relative w-full h-full flex items-center justify-center min-h-[400px]"
        style={{ perspective: 1200 }}
      >
        <div
          className={`absolute flex items-center justify-center transition-transform duration-700 ease-out ${glowPulse}`}
          style={{
            transformStyle: 'preserve-3d',
            transform: `scale(${zoom}) rotateX(60deg) rotateZ(${rotation}deg)`,
          }}
        >
          {/* Ground Grid */}
          <div
            className="absolute top-1/2 left-1/2 border border-slate-700/50 rounded-full"
            style={{
              width: maxDim * scale * 2.5,
              height: maxDim * scale * 2.5,
              transform: `translate(-50%, -50%) translateZ(-1px)`,
              backgroundImage: 'linear-gradient(to right, rgba(34, 211, 238, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(34, 211, 238, 0.1) 1px, transparent 1px)',
              backgroundSize: '20px 20px',
              backgroundPosition: 'center center'
            }}
          />

          {/* Floor */}
          <div
            className={wireframeBase + " bg-cyan-950/60"}
            style={{ width: l, height: w, transform: `translate(-50%, -50%) translateZ(0)` }}
          >
             <GridLines />
          </div>

          {/* South Wall (Front) */}
          <div
            className={wireframeBase + " flex items-end justify-center"}
            style={{ width: l, height: h, transform: `translate(-50%, -50%) translateY(${w/2}px) translateZ(${h/2}px) rotateX(-90deg)` }}
          >
             {/* Door cutout */}
             <div className="border border-cyan-300/80 bg-cyan-400/10 shadow-[0_0_10px_rgba(34,211,238,0.4)_inset]" style={{ width: l * 0.15, height: h * 0.7 }} />
          </div>

          {/* North Wall (Back) */}
          <div
            className={wireframeBase}
            style={{ width: l, height: h, transform: `translate(-50%, -50%) translateY(${-w/2}px) translateZ(${h/2}px) rotateX(90deg)` }}
          >
             <GridLines />
          </div>

          {/* West Wall (Left) */}
          <div
            className={wireframeBase + " flex items-center justify-center"}
            style={{ width: w, height: h, transform: `translate(-50%, -50%) translateX(${-l/2}px) translateZ(${h/2}px) rotateY(-90deg) rotateZ(90deg)` }}
          >
             {/* Window cutout */}
             <div className="border border-cyan-300/80 bg-cyan-400/10 shadow-[0_0_10px_rgba(34,211,238,0.4)_inset]" style={{ width: w * 0.4, height: h * 0.35 }} />
          </div>

          {/* East Wall (Right) */}
          <div
            className={wireframeBase + " flex items-center justify-center"}
            style={{ width: w, height: h, transform: `translate(-50%, -50%) translateX(${l/2}px) translateZ(${h/2}px) rotateY(90deg) rotateZ(-90deg)` }}
          >
             {/* Window cutout */}
             <div className="border border-cyan-300/80 bg-cyan-400/10 shadow-[0_0_10px_rgba(34,211,238,0.4)_inset]" style={{ width: w * 0.4, height: h * 0.35 }} />
          </div>

          {/* Roof Structure */}
          {geometry.roofType === 'pitched' ? (
            <>
              {/* South Roof Pitch */}
              <div
                className={wireframeBase + " bg-cyan-900/40 border-cyan-300"}
                style={{
                  width: l,
                  height: roofSideLength,
                  transform: `translate(-50%, -50%) translateY(${w/4}px) translateZ(${h + rh/2}px) rotateX(-${roofAngleDeg}deg)`,
                }}
              >
                 <GridLines />
              </div>

              {/* North Roof Pitch */}
              <div
                className={wireframeBase + " bg-cyan-900/40 border-cyan-300"}
                style={{
                  width: l,
                  height: roofSideLength,
                  transform: `translate(-50%, -50%) translateY(${-w/4}px) translateZ(${h + rh/2}px) rotateX(${roofAngleDeg}deg)`,
                }}
              >
                 <GridLines />
              </div>

              {/* West Gable (Triangle) */}
              <div
                className="absolute top-1/2 left-1/2 bg-cyan-400/20"
                style={{
                  width: w,
                  height: rh,
                  clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)',
                  transform: `translate(-50%, -50%) translateX(${-l/2}px) translateZ(${h + rh/2}px) rotateY(-90deg) rotateZ(90deg)`,
                }}
              >
                 {/* Internal truss lines */}
                 <div className="absolute bottom-0 left-1/2 w-px h-full bg-cyan-400/80 -translate-x-1/2"></div>
              </div>

              {/* East Gable (Triangle) */}
              <div
                className="absolute top-1/2 left-1/2 bg-cyan-400/20"
                style={{
                  width: w,
                  height: rh,
                  clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)',
                  transform: `translate(-50%, -50%) translateX(${l/2}px) translateZ(${h + rh/2}px) rotateY(90deg) rotateZ(-90deg)`,
                }}
              >
                 <div className="absolute bottom-0 left-1/2 w-px h-full bg-cyan-400/80 -translate-x-1/2"></div>
              </div>
            </>
          ) : (
            <div
              className={wireframeBase + " bg-cyan-900/40"}
              style={{ width: l, height: w, transform: `translate(-50%, -50%) translateZ(${h}px)` }}
            >
               <GridLines />
            </div>
          )}
        </div>
      </div>

      {/* Controls Overlay */}
      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between z-10 bg-slate-900/80 backdrop-blur-md p-2 rounded-lg border border-slate-800 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(z + 0.2, 2))}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 transition-colors cursor-pointer pointer-events-auto"
            aria-label="Zoom in"
          >
            <ZoomIn size={16} />
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.5))}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 transition-colors cursor-pointer pointer-events-auto"
            aria-label="Zoom out"
          >
            <ZoomOut size={16} />
          </button>
        </div>
        
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono font-medium text-cyan-400 bg-cyan-950/50 px-2.5 py-1 rounded border border-cyan-900/50">
            {geometry.orientation}-facing · {geometry.roofType.toUpperCase()}
          </span>
          <button
            type="button"
            onClick={() => setUserRotation((r) => r + 45)}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 transition-colors flex items-center gap-2 pointer-events-auto text-xs font-medium cursor-pointer shadow-[0_0_10px_rgba(34,211,238,0.1)] hover:shadow-[0_0_15px_rgba(34,211,238,0.2)]"
          >
            <RotateCw size={14} /> Orbit View
          </button>
        </div>
      </div>
      
      {/* HUD Info */}
      <div className="absolute top-4 left-4 z-20 pointer-events-none bg-slate-900/60 backdrop-blur-sm p-2 rounded border border-cyan-900/30">
        <div className="text-[10px] font-mono text-cyan-400 tracking-widest uppercase mb-1 drop-shadow-md">Thermal Simulation Model</div>
        <div className="text-xs font-mono text-cyan-200 drop-shadow-md">{geometry.lengthM}m × {geometry.widthM}m × {geometry.heightM}m</div>
        {isSimulating && (
          <div className="mt-2 text-[10px] font-mono text-amber-400 animate-pulse flex items-center gap-1.5 drop-shadow-md">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_5px_#fbbf24]"></span> SOLVER ACTIVE
          </div>
        )}
      </div>
    </div>
  )
}
