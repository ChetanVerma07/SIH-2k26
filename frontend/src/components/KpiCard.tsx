import type { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface KpiCardProps {
  label: string
  value: string
  unit?: string
  icon: LucideIcon
  tone?: 'default' | 'good' | 'alert' | 'solar'
}

const toneClasses: Record<string, string> = {
  default: 'text-slate-900',
  good: 'text-good',
  alert: 'text-red-600',
  solar: 'text-solar',
}

export function KpiCard({ label, value, unit, icon: Icon, tone = 'default' }: KpiCardProps) {
  return (
    <div className="tick-panel p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-slate-500">{label}</span>
        <Icon size={16} className="text-brand-600" strokeWidth={1.75} />
      </div>
      <div className={clsx('font-display text-2xl font-semibold', toneClasses[tone])}>
        {value}
        {unit && <span className="text-sm text-slate-500 font-mono ml-1">{unit}</span>}
      </div>
    </div>
  )
}
