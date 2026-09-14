import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HeatFlowBreakdown as HeatFlowBreakdownType } from '../types'

interface HeatFlowBreakdownProps {
  breakdown: HeatFlowBreakdownType
}

const COLORS = ['#1D3A5F', '#3E8FB0', '#64748b', '#B5482E']

export function HeatFlowBreakdown({ breakdown }: HeatFlowBreakdownProps) {
  const total = breakdown.walls + breakdown.roof + breakdown.floor + breakdown.openings || 1
  const data = [
    { name: 'Walls', value: breakdown.walls, pct: (breakdown.walls / total) * 100 },
    { name: 'Roof', value: breakdown.roof, pct: (breakdown.roof / total) * 100 },
    { name: 'Floor', value: breakdown.floor, pct: (breakdown.floor / total) * 100 },
    { name: 'Openings', value: breakdown.openings, pct: (breakdown.openings / total) * 100 },
  ]

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
          <CartesianGrid stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }} stroke="#64748b" />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }}
            stroke="#64748b"
            width={70}
          />
          <Tooltip
            contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 0, fontSize: 12, fontFamily: 'IBM Plex Mono' }}
            formatter={(value: number, _name, entry) => [
              `${value.toLocaleString()} Wh (${(entry.payload as { pct: number }).pct.toFixed(1)}%)`,
              'Heat loss',
            ]}
          />
          <Bar dataKey="value" radius={0}>
            {data.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-4 gap-2 mt-2">
        {data.map((d, idx) => (
          <div key={d.name} className="text-center">
            <div className="w-full h-1 mb-1" style={{ background: COLORS[idx % COLORS.length] }} />
            <p className="text-xs font-mono text-slate-900">{d.pct.toFixed(0)}%</p>
            <p className="text-[11px] text-slate-500">{d.name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
