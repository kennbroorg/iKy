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

/**
 * Safely extract a value from graphic[] by key alone (index-independent).
 *
 * Scans the entire graphic array for the first item containing `key`.
 * Use this when the backend conditionally appends items, making indices
 * unstable (e.g. keybase, or search vs dorks which have different counts).
 */
export function gfxByKey<T = unknown>(
  graphic: GraphicItem[],
  key: string,
): T | undefined {
  for (const item of graphic) {
    if (item && key in item) {
      return item[key] as T | undefined;
    }
  }
  return undefined;
}
