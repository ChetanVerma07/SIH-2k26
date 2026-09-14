import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts'
import type { TimeSeriesPoint } from '../types'

interface TemperatureChartProps {
  series: TimeSeriesPoint[]
}

export function TemperatureChart({ series }: TemperatureChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={series} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#e2e8f0" vertical={false} />
        <XAxis
          dataKey="hour"
          tickFormatter={(h: number) => `${Math.round(h)}:00`}
          stroke="#64748b"
          tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
          label={{ value: 'Time', position: 'insideBottom', offset: -2, fontSize: 11, fill: '#64748b' }}
        />
        <YAxis
          stroke="#64748b"
          tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
          label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#64748b' }}
        />
        <Tooltip
          contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 0, fontSize: 12, fontFamily: 'IBM Plex Mono' }}
          formatter={(value: number) => `${value.toFixed(1)} °C`}
          labelFormatter={(h: number) => `Hour ${Math.round(h)}:00`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="ambientTempC" name="Ambient" stroke="#64748b" strokeWidth={1.5} dot={false} />
        <Line type="monotone" dataKey="indoorTempC" name="Indoor" stroke="#3E8FB0" strokeWidth={2.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
