import type { ComponentType } from "react";

export type ModuleCategory =
  | "social"
  | "email"
  | "search"
  | "leak"
  | "enrichment"
  | "username";

export type InputType = "email" | "username" | "both";

export interface ModuleConfig {
  id: string;
  label: string;
  icon: string;
  category: ModuleCategory;
  inputType: InputType;
  requiresApiKey?: string;
  specialParams?: Record<string, unknown>;
  visualization: {
    useGenericGraph?: boolean;
    useGenericChart?: boolean;
    useGenericTable?: boolean;
    customComponent?: ComponentType<{ data: unknown }>;
  };
}
