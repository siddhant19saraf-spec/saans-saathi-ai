"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type ComparisonPoint = { label: string; value: number };

export function ComparisonBarChart({
  data,
  label,
  unit,
  height = 240,
}: {
  data: ComparisonPoint[];
  label: string;
  unit: string;
  height?: number;
}) {
  const summary =
    data.length === 0
      ? `${label}: no values available`
      : `${label}: ${data.map((point) => `${point.label} ${point.value} ${unit}`).join(", ")}`;

  return (
    <figure>
      <div role="img" aria-label={summary} style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid stroke="var(--color-line)" strokeDasharray="4 4" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "var(--color-ink-muted)" }}
              axisLine={false}
              tickLine={false}
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
            <Bar
              dataKey="value"
              name={label}
              fill="var(--color-brand-600)"
              radius={[6, 6, 0, 0]}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="sr-only">
        <table>
          <caption>{label} comparison</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((point) => (
              <tr key={point.label}>
                <th scope="row">{point.label}</th>
                <td>
                  {point.value} {unit}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </figcaption>
    </figure>
  );
}
