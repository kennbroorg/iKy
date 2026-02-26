import type { ModuleResultRaw } from "@/types/api";

export function parseModuleResult(
  resultArray: Record<string, unknown>[],
): ModuleResultRaw {
  const findValue = (key: string) =>
    resultArray.find((item) => key in item)?.[key];

  return {
    module: (findValue("module") as string) ?? "",
    param: (findValue("param") as string) ?? "",
    validation:
      (findValue("validation") as ModuleResultRaw["validation"]) ?? "not_used",
    raw: (findValue("raw") as Record<string, unknown>) ?? {},
    graphic: (findValue("graphic") as ModuleResultRaw["graphic"]) ?? [],
    profile: (findValue("profile") as ModuleResultRaw["profile"]) ?? [],
    timeline: (findValue("timeline") as ModuleResultRaw["timeline"]) ?? [],
    tasks: (findValue("tasks") as ModuleResultRaw["tasks"]) ?? [],
    // GhostProject stores leaks at top level instead of in graphic[]
    leaks: findValue("leaks") as ModuleResultRaw["leaks"],
  };
}
