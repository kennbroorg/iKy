import { ResponsiveContainer, Treemap } from "recharts";

/** Cyan/teal palette for treemap cells */
const TREEMAP_COLORS = [
  "#06b6d4", // cyan-500
  "#14b8a6", // teal-500
  "#0891b2", // cyan-600
  "#0d9488", // teal-600
  "#22d3ee", // cyan-400
  "#2dd4bf", // teal-400
] as const;

interface TreemapDatum {
  name: string;
  total?: number;
  value?: number;
  size?: number;
}

interface NormalizedNode {
  name: string;
  size: number;
}

interface TreemapChartProps {
  data: TreemapDatum[];
  height?: number;
}

/**
 * Normalize treemap input data to `{name, size}[]`.
 * Accepts items with `total`, `value`, or `size` fields (checked in that order).
 */
export function normalizeTreemapData(data: TreemapDatum[]): NormalizedNode[] {
  if (!data || data.length === 0) return [];
  return data.map((d) => ({
    name: d.name,
    size: d.total ?? d.value ?? d.size ?? 0,
  }));
}

/** Format large numbers with K/M suffixes */
function formatValue(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
  return String(v);
}

/**
 * Custom content renderer for Recharts Treemap cells.
 * Renders a colored rect with name and value text.
 */
function TreemapContent(props: {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  index?: number;
  name?: string;
  size?: number;
  depth?: number;
}) {
  const { x = 0, y = 0, width = 0, height = 0, index = 0, name, size, depth } = props;

  // Only render leaf nodes (depth === 1 for flat data)
  if (depth !== 1) return null;

  const fill = TREEMAP_COLORS[index % TREEMAP_COLORS.length];
  const showLabel = width > 40 && height > 24;
  const showValue = width > 50 && height > 40;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={3}
        ry={3}
        fill={fill}
        fillOpacity={0.85}
        stroke="rgba(0,0,0,0.3)"
        strokeWidth={1}
      />
      {showLabel && (
        <text
          x={x + width / 2}
          y={y + height / 2 - (showValue ? 6 : 0)}
          textAnchor="middle"
          dominantBaseline="central"
          fill="white"
          fontSize={Math.min(12, width / 6)}
          fontWeight={500}
        >
          {name}
        </text>
      )}
      {showValue && size !== undefined && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 10}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.7)"
          fontSize={Math.min(10, width / 8)}
        >
          {formatValue(size)}
        </text>
      )}
    </g>
  );
}

/**
 * Treemap visualization built on Recharts.
 * Accepts data with `total`, `value`, or `size` numeric fields.
 */
export function TreemapChart({ data, height = 250 }: TreemapChartProps) {
  const normalized = normalizeTreemapData(data);

  if (normalized.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No treemap data available.
      </p>
    );
  }

  // Recharts Treemap expects a `children` array inside a root object
  const treemapData = [{ name: "root", children: normalized }];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Treemap
        data={treemapData}
        dataKey="size"
        nameKey="name"
        stroke="none"
        content={<TreemapContent />}
      />
    </ResponsiveContainer>
  );
}
