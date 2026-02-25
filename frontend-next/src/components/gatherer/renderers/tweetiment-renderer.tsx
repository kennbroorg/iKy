import { ModuleChart } from "@/components/viz/module-chart";

import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Tweetiment module (Twitter sentiment analysis).
 *
 * Reads 1 visualization from `result.graphic[0]`:
 *  0 sentiment — Multi-series line chart data
 */
export function TweetimentRenderer({ result }: RendererProps) {
  const sentiment = gfx<Record<string, unknown>[]>(
    result.graphic,
    0,
    "sentiment",
  );

  if (!sentiment || sentiment.length === 0) return null;

  return (
    <VizCard title="Sentiment Analysis">
      <ModuleChart data={sentiment} type="line" height={300} />
    </VizCard>
  );
}
