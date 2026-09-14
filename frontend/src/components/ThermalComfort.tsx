import { CheckCircle2, XCircle } from 'lucide-react'
import type { SimulationResult } from '../types'
import { NumberField } from './ui'

interface ThermalComfortProps {
  comfortMin: number
  comfortMax: number
  onChangeMin: (val: number) => void
  onChangeMax: (val: number) => void
  result: SimulationResult | null
}

export function ThermalComfort({ comfortMin, comfortMax, onChangeMin, onChangeMax, result }: ThermalComfortProps) {
  const passes = result ? result.comfortPercentage >= 70 : null

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="grid grid-cols-2 gap-3">
        <NumberField
          label="Comfort minimum"
          unit="°C"
          value={comfortMin}
          onChange={onChangeMin}
          step={0.5}
        />
        <NumberField
          label="Comfort maximum"
          unit="°C"
          value={comfortMax}
          onChange={onChangeMax}
          step={0.5}
        />
      </div>

      {result ? (
        <div>
          <div className="w-full h-3 bg-slate-200 flex overflow-hidden mb-2">
            <div className="h-full bg-blue-500/50" style={{ width: `${(100 - result.comfortPercentage) / 2}%` }} title="Below comfort" />
            <div className="h-full bg-green-500" style={{ width: `${result.comfortPercentage}%` }} title="Within comfort" />
            <div className="h-full bg-amber-500" style={{ width: `${(100 - result.comfortPercentage) / 2}%` }} title="Above comfort" />
          </div>
          <div className="flex justify-between text-xs font-mono text-slate-500 mb-3">
            <span>{((100 - result.comfortPercentage) / 2).toFixed(1)}% below</span>
            <span className="text-green-600">{result.comfortPercentage}% within range</span>
            <span>{((100 - result.comfortPercentage) / 2).toFixed(1)}% above</span>
          </div>
          <div className="flex items-center gap-2 text-sm font-medium">
            {passes ? (
              <>
                <CheckCircle2 size={16} className="text-green-600" />
                <span className="text-green-600">Design meets the selected comfort target</span>
              </>
            ) : (
              <>
                <XCircle size={16} className="text-red-600" />
                <span className="text-red-600">Design falls short of the selected comfort target</span>
              </>
            )}
          </div>
        </div>
      ) : (
        <p className="text-sm text-slate-500 flex items-center">Run a simulation to see comfort results.</p>
      )}
    </div>
  )
}
