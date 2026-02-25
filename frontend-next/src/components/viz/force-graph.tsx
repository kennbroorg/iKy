import { useCallback, useEffect, useRef, useState } from "react";

import ForceGraph2D from "react-force-graph-2d";
import type { NodeObject } from "react-force-graph-2d";

/** Color palette for node groups */
const GROUP_COLORS = [
  "#06b6d4", // cyan-500
  "#14b8a6", // teal-500
  "#0891b2", // cyan-600
  "#0d9488", // teal-600
  "#22d3ee", // cyan-400
  "#2dd4bf", // teal-400
  "#67e8f9", // cyan-300
  "#5eead4", // teal-300
] as const;

interface ForceGraphNode {
  id: string;
  label: string;
  img?: string;
  group?: string;
}

interface ForceGraphLink {
  source: string;
  target: string;
}

interface ForceGraphProps {
  nodes: ForceGraphNode[];
  links: ForceGraphLink[];
  width?: number;
  height?: number;
}

/**
 * Wrapper around ForceGraph2D for rendering force-directed graphs
 * with a dark theme and cyan/teal accent colors.
 */
export function ForceGraph({
  nodes,
  links,
  width,
  height,
}: ForceGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(undefined);
  const [dimensions, setDimensions] = useState({ w: width ?? 600, h: height ?? 400 });

  // Build a group -> color mapping
  const groupColorMap = useRef(new Map<string, string>());

  const getGroupColor = useCallback((group?: string): string => {
    if (!group) return GROUP_COLORS[0];
    const map = groupColorMap.current;
    if (!map.has(group)) {
      map.set(group, GROUP_COLORS[map.size % GROUP_COLORS.length]);
    }
    return map.get(group)!;
  }, []);

  // Responsive sizing: observe container width/height
  useEffect(() => {
    if (width && height) return; // Skip if explicit dimensions provided
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width: w, height: h } = entry.contentRect;
      setDimensions({
        w: width ?? Math.max(w, 200),
        h: height ?? Math.max(h, 300),
      });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [width, height]);

  // Zoom to fit after initial render
  useEffect(() => {
    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(400, 40);
    }, 500);
    return () => clearTimeout(timer);
  }, [nodes, links]);

  const graphData = { nodes: [...nodes], links: [...links] };

  const nodeCanvasObject = useCallback(
    (
      node: NodeObject<ForceGraphNode>,
      ctx: CanvasRenderingContext2D,
      globalScale: number,
    ) => {
      const label = node.label || node.id || "";
      const fontSize = Math.max(10 / globalScale, 1.5);
      const nodeRadius = 4;
      const x = node.x ?? 0;
      const y = node.y ?? 0;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = getGroupColor(node.group);
      ctx.fill();

      // Draw glow effect
      ctx.shadowColor = getGroupColor(node.group);
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Draw label below
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
      ctx.fillText(label, x, y + nodeRadius + 2);
    },
    [getGroupColor],
  );

  const nodePointerAreaPaint = useCallback(
    (
      node: NodeObject<ForceGraphNode>,
      color: string,
      ctx: CanvasRenderingContext2D,
    ) => {
      const nodeRadius = 6;
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, nodeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    [],
  );

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-md"
      style={{ minHeight: height ?? 400 }}
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.w}
        height={dimensions.h}
        backgroundColor="rgba(0,0,0,0)"
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={() => "replace"}
        nodePointerAreaPaint={nodePointerAreaPaint}
        linkColor={() => "rgba(113, 113, 122, 0.4)"}
        linkWidth={1}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        cooldownTicks={100}
        nodeLabel={(node: NodeObject<ForceGraphNode>) =>
          node.label || String(node.id ?? "")
        }
      />
    </div>
  );
}
