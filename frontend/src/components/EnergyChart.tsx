import { Area, AreaChart, CartesianGrid, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { TimeSeriesPoint } from '../types'

interface EnergyChartProps {
  series: TimeSeriesPoint[]
}

export function EnergyChart({ series }: EnergyChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={series} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#e2e8f0" vertical={false} />
        <XAxis
          dataKey="hour"
          tickFormatter={(h: number) => `${Math.round(h)}:00`}
          stroke="#64748b"
          tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
        />
        <YAxis
          stroke="#64748b"
          tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
          label={{ value: 'Power (W)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#64748b' }}
        />
        <Tooltip
          contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 0, fontSize: 12, fontFamily: 'IBM Plex Mono' }}
          formatter={(value: number) => `${value.toFixed(0)} W`}
          labelFormatter={(h: number) => `Hour ${Math.round(h)}:00`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          type="monotone"
          dataKey="solarGainW"
          name="Solar gain"
          stroke="#C97A3D"
          fill="#C97A3D"
          fillOpacity={0.18}
          strokeWidth={2}
        />
        <Line type="monotone" dataKey="wallLossW" name="Wall loss" stroke="#1D3A5F" strokeWidth={1.25} dot={false} />
        <Line type="monotone" dataKey="roofLossW" name="Roof loss" stroke="#3E8FB0" strokeWidth={1.25} dot={false} />
        <Line type="monotone" dataKey="floorLossW" name="Floor loss" stroke="#64748b" strokeWidth={1.25} dot={false} />
        <Line
          type="monotone"
          dataKey="openingLossW"
          name="Opening loss"
          stroke="#B5482E"
          strokeWidth={1.25}
          dot={false}
        />
        <Line type="monotone" dataKey="totalLossW" name="Total loss" stroke="#14233D" strokeWidth={2.25} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
