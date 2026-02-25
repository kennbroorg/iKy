import type { GraphicItem, ModuleResultRaw } from "@/types/api";

/** Props passed to every custom module renderer */
export interface RendererProps {
  result: ModuleResultRaw;
}

/**
 * Safely extract a value from graphic[] at a given index and key.
 * Returns undefined if the path doesn't exist.
 */
export function gfx<T = unknown>(
  graphic: GraphicItem[],
  index: number,
  key: string,
): T | undefined {
  const item = graphic[index];
  if (!item) return undefined;
  return item[key] as T | undefined;
}
