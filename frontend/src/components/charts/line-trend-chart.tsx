"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type TrendPoint = { label: string; value: number | null };

export function LineTrendChart({
  data,
  label,
  unit,
  height = 240,
}: {
  data: TrendPoint[];
  label: string;
  unit: string;
  height?: number;
}) {
  const values = data.flatMap((point) => (point.value === null ? [] : [point.value]));
  const summary =
    values.length === 0
      ? `${label}: no values available`
      : `${label}: ${values.length} values, from ${Math.min(...values)} to ${Math.max(...values)} ${unit}`;

  return (
    <figure>
      <div role="img" aria-label={summary} style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <defs>
              <linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-brand-500)" stopOpacity={0.28} />
                <stop offset="100%" stopColor="var(--color-brand-500)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-line)" strokeDasharray="4 4" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "var(--color-ink-muted)" }}
              axisLine={false}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "var(--color-ink-muted)" }}
              axisLine={false}
              tickLine={false}
              width={48}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid var(--color-line)",
                fontSize: 12,
              }}
              formatter={(value) => [`${String(value)} ${unit}`, label]}
            />
            <Area
              type="monotone"
              dataKey="value"
              name={label}
              stroke="var(--color-brand-700)"
              strokeWidth={2}
              fill="url(#trend-fill)"
              connectNulls={false}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="sr-only">
        <table>
          <caption>
            {label} values in {unit}
          </caption>
          <thead>
            <tr>
              <th scope="col">Time</th>
              <th scope="col">Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((point) => (
              <tr key={point.label}>
                <th scope="row">{point.label}</th>
                <td>{point.value === null ? "Not reported" : point.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </figcaption>
    </figure>
  );
}
