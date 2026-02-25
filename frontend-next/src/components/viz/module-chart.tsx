import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/** Cyan/teal palette for chart elements */
const CHART_COLORS = [
  "#06b6d4", // cyan-500
  "#14b8a6", // teal-500
  "#22d3ee", // cyan-400
  "#2dd4bf", // teal-400
  "#0891b2", // cyan-600
  "#0d9488", // teal-600
  "#67e8f9", // cyan-300
  "#5eead4", // teal-300
] as const;

interface ModuleChartProps {
  data: Record<string, unknown>[];
  type?: "bar" | "pie" | "line";
  dataKey?: string;
  nameKey?: string;
  /** Pie chart variant: "donut" (innerRadius=60), "full-pie" (0), default (40) */
  variant?: "default" | "donut" | "full-pie";
  /** Bar chart layout: "horizontal" renders bars horizontally via BarChart layout="vertical" */
  layout?: "vertical" | "horizontal";
  /** Chart height in px (default 300) */
  height?: number;
}

/** Date-like patterns for auto-detection */
const DATE_PATTERN = /^\d{4}[-/]\d{2}([-/]\d{2})?$/;

/**
 * Detect whether a value is numeric (or numeric string).
 */
function isNumericValue(v: unknown): boolean {
  if (typeof v === "number") return true;
  if (typeof v === "string") return !isNaN(Number(v)) && v.trim() !== "";
  return false;
}

/**
 * Auto-detect the best chart type for the given data.
 */
function detectChartType(
  data: Record<string, unknown>[],
): "bar" | "pie" | "line" {
  if (data.length === 0) return "bar";

  const firstRow = data[0];
  const keys = Object.keys(firstRow);

  // Check for date-like keys
  const hasDateKey = keys.some(
    (k) =>
      DATE_PATTERN.test(String(firstRow[k] ?? "")) ||
      k.toLowerCase().includes("date") ||
      k.toLowerCase().includes("time"),
  );
  if (hasDateKey && data.length > 1) return "line";

  // Count numeric values in first row
  const numericCount = keys.filter((k) =>
    isNumericValue(firstRow[k]),
  ).length;

  // If small dataset with numeric values, consider pie for distributions
  if (data.length <= 8 && numericCount >= 1) {
    // Check if it looks like a distribution (values sum to ~100 or all positive)
    const numericKey = keys.find((k) => isNumericValue(firstRow[k]));
    if (numericKey) {
      const values = data.map((d) => Number(d[numericKey]));
      const sum = values.reduce((a, b) => a + b, 0);
      if (sum > 0 && values.every((v) => v >= 0)) {
        if (Math.abs(sum - 100) < 5) return "pie";
      }
    }
  }

  // Default to bar for datasets under 10 items
  if (data.length < 10 && numericCount >= 1) return "bar";

  return "bar";
}

/**
 * Find the first numeric key in the data (for dataKey default).
 */
function findNumericKey(data: Record<string, unknown>[]): string | undefined {
  if (data.length === 0) return undefined;
  return Object.keys(data[0]).find((k) => isNumericValue(data[0][k]));
}

/**
 * Find the first non-numeric key in the data (for nameKey default).
 */
function findNameKey(data: Record<string, unknown>[]): string | undefined {
  if (data.length === 0) return undefined;
  return Object.keys(data[0]).find((k) => !isNumericValue(data[0][k]));
}

/** Custom dark tooltip */
function DarkTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: unknown; color: string }>;
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg">
      {label && (
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          {label}
        </p>
      )}
      {payload.map((entry, i) => (
        <p key={i} className="text-sm text-foreground">
          <span style={{ color: entry.color }} className="mr-1.5">
            {"\u25CF"}
          </span>
          {entry.name}: {String(entry.value)}
        </p>
      ))}
    </div>
  );
}

/**
 * Flexible chart component that auto-selects the chart type
 * and renders with a dark hacker theme.
 */
export function ModuleChart({
  data,
  type,
  dataKey,
  nameKey,
  variant = "default",
  layout = "vertical",
  height = 300,
}: ModuleChartProps) {
  if (!data || data.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No chart data available.
      </p>
    );
  }

  const chartType = type ?? detectChartType(data);
  const resolvedDataKey = dataKey ?? findNumericKey(data) ?? "value";
  const resolvedNameKey = nameKey ?? findNameKey(data) ?? "name";

  // Ensure data values are numeric for the data key
  const cleanData = data.map((d) => ({
    ...d,
    [resolvedDataKey]: Number(d[resolvedDataKey] ?? 0),
  }));

  const pieInnerRadius =
    variant === "donut" ? 60 : variant === "full-pie" ? 0 : 40;

  if (chartType === "pie") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={cleanData}
            dataKey={resolvedDataKey}
            nameKey={resolvedNameKey}
            cx="50%"
            cy="50%"
            outerRadius={100}
            innerRadius={pieInnerRadius}
            strokeWidth={1}
            stroke="rgba(39, 39, 42, 0.8)"
            label={({ name, percent }: { name?: string; percent?: number }) =>
              `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
            }
            labelLine={{ stroke: "rgba(161, 161, 170, 0.5)" }}
          >
            {cleanData.map((_, i) => (
              <Cell
                key={i}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip content={<DarkTooltip />} />
          <Legend
            wrapperStyle={{ color: "rgba(228, 228, 231, 0.8)", fontSize: 12 }}
          />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={cleanData}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(63, 63, 70, 0.5)"
          />
          <XAxis
            dataKey={resolvedNameKey}
            tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
            axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
            tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
          />
          <YAxis
            tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
            axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
            tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
          />
          <Tooltip content={<DarkTooltip />} />
          <Line
            type="monotone"
            dataKey={resolvedDataKey}
            stroke={CHART_COLORS[0]}
            strokeWidth={2}
            dot={{ fill: CHART_COLORS[0], r: 3 }}
            activeDot={{ r: 5, fill: CHART_COLORS[2] }}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  // Horizontal layout: BarChart with layout="vertical", swapped axes
  if (layout === "horizontal") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={cleanData} layout="vertical">
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(63, 63, 70, 0.5)"
          />
          <XAxis
            type="number"
            tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
            axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
            tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
          />
          <YAxis
            type="category"
            dataKey={resolvedNameKey}
            tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
            axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
            tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
            width={100}
          />
          <Tooltip content={<DarkTooltip />} />
          <Bar dataKey={resolvedDataKey} radius={[0, 4, 4, 0]}>
            {cleanData.map((_, i) => (
              <Cell
                key={i}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  // Default: vertical bar chart
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={cleanData}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(63, 63, 70, 0.5)"
        />
        <XAxis
          dataKey={resolvedNameKey}
          tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
          axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
          tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
        />
        <YAxis
          tick={{ fill: "rgba(161, 161, 170, 0.8)", fontSize: 11 }}
          axisLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
          tickLine={{ stroke: "rgba(63, 63, 70, 0.5)" }}
        />
        <Tooltip content={<DarkTooltip />} />
        <Bar
          dataKey={resolvedDataKey}
          radius={[4, 4, 0, 0]}
        >
          {cleanData.map((_, i) => (
            <Cell
              key={i}
              fill={CHART_COLORS[i % CHART_COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
