import { useEffect, useRef, useState } from "react";

import { hierarchy, pack } from "d3-hierarchy";

/** Cyan/teal palette for bubbles */
const BUBBLE_COLORS = [
  "#06b6d4", // cyan-500
  "#14b8a6", // teal-500
  "#0891b2", // cyan-600
  "#0d9488", // teal-600
  "#22d3ee", // cyan-400
  "#2dd4bf", // teal-400
] as const;

interface BubbleDatum {
  name: string;
  value: number;
}

interface PositionedBubble {
  name: string;
  value: number;
  x: number;
  y: number;
  r: number;
}

interface BubbleChartProps {
  data: BubbleDatum[];
  height?: number;
}

/**
 * Compute circle-packing layout using d3-hierarchy's `pack()`.
 * Returns positioned bubbles with x, y, and radius.
 */
export function computeBubbleLayout(
  data: BubbleDatum[],
  width: number,
  height: number,
): PositionedBubble[] {
  if (!data || data.length === 0) return [];

  const root = hierarchy({ children: data } as {
    children: BubbleDatum[];
  })
    .sum((d) => {
      // The root node has `children`, leaf nodes have `value`
      const datum = d as unknown as BubbleDatum;
      return datum.value ?? 0;
    })
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const packLayout = pack<{ children: BubbleDatum[] }>()
    .size([width, height])
    .padding(4);

  packLayout(root);

  // Return only leaf nodes (the actual data items)
  return (root.leaves() as { data: BubbleDatum; x: number; y: number; r: number }[]).map(
    (leaf) => ({
      name: leaf.data.name,
      value: leaf.data.value,
      x: leaf.x,
      y: leaf.y,
      r: leaf.r,
    }),
  );
}

/**
 * Bubble chart using d3-hierarchy circle packing.
 * Renders SVG circles with labels for bubbles large enough to fit text.
 */
export function BubbleChart({ data, height = 300 }: BubbleChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(400);

  // Track container width via ResizeObserver
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width: w } = entry.contentRect;
      if (w > 0) setContainerWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  if (!data || data.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No bubble data available.
      </p>
    );
  }

  const bubbles = computeBubbleLayout(data, containerWidth, height);

  return (
    <div ref={containerRef} className="w-full">
      <svg
        width={containerWidth}
        height={height}
        viewBox={`0 0 ${containerWidth} ${height}`}
        className="overflow-visible"
      >
        {bubbles.map((bubble, i) => {
          const fill = BUBBLE_COLORS[i % BUBBLE_COLORS.length];
          const showText = bubble.r > 20;
          const fontSize = Math.max(8, Math.min(14, bubble.r / 4));

          return (
            <g key={bubble.name}>
              <circle
                cx={bubble.x}
                cy={bubble.y}
                r={bubble.r}
                fill={fill}
                fillOpacity={0.8}
                stroke={fill}
                strokeOpacity={0.4}
                strokeWidth={1}
              />
              {showText && (
                <>
                  <text
                    x={bubble.x}
                    y={bubble.y - fontSize * 0.3}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill="white"
                    fontSize={fontSize}
                    fontWeight={500}
                  >
                    {bubble.name}
                  </text>
                  <text
                    x={bubble.x}
                    y={bubble.y + fontSize * 0.9}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill="rgba(255,255,255,0.7)"
                    fontSize={fontSize * 0.8}
                  >
                    {bubble.value}
                  </text>
                </>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
