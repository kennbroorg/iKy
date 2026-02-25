import { describe, expect, it } from "vitest";

import {
  getModule,
  getModulesByCategory,
  getModulesForInput,
  MODULE_REGISTRY,
} from "../module-registry";

describe("module-registry", () => {
  it("has 28 modules", () => {
    expect(MODULE_REGISTRY.length).toBe(28);
  });

  it("filters by category", () => {
    const leaks = getModulesByCategory("leak");
    expect(leaks.every((m) => m.category === "leak")).toBe(true);
    expect(leaks.length).toBeGreaterThan(0);
  });

  it("finds module by id", () => {
    expect(getModule("github")?.label).toBe("GitHub");
  });

  it("filters email modules for email input", () => {
    const mods = getModulesForInput("test@example.com");
    expect(
      mods.every((m) => m.inputType === "email" || m.inputType === "both"),
    ).toBe(true);
  });

  it("filters username modules for username input", () => {
    const mods = getModulesForInput("johndoe");
    expect(
      mods.every((m) => m.inputType === "username" || m.inputType === "both"),
    ).toBe(true);
  });
});
