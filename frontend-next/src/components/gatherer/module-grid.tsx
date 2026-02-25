import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getModuleIcon } from "@/lib/icon-map";
import { getModulesByCategory, MODULE_REGISTRY } from "@/lib/module-registry";
import { useGatherStore, type TaskStatus } from "@/stores/gather-store";
import { useUiStore } from "@/stores/ui-store";
import type { ModuleCategory } from "@/types/modules";

const CATEGORIES: Array<{ value: ModuleCategory | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "social", label: "Social" },
  { value: "leak", label: "Leak" },
  { value: "email", label: "Email" },
  { value: "username", label: "Username" },
  { value: "search", label: "Search" },
  { value: "enrichment", label: "Enrichment" },
];

function StatusIndicator({ status }: { status: TaskStatus | undefined }) {
  if (!status || status === "idle") {
    return (
      <span className="inline-block size-2 rounded-full bg-muted-foreground/40" />
    );
  }

  if (
    status === "dispatching" ||
    status === "pending" ||
    status === "running"
  ) {
    return (
      <Loader2 className="size-3.5 animate-spin text-primary" />
    );
  }

  if (status === "success") {
    return <CheckCircle2 className="size-3.5 text-emerald-400" />;
  }

  if (status === "error") {
    return <XCircle className="size-3.5 text-red-400" />;
  }

  return null;
}

export function ModuleGrid() {
  const tasks = useGatherStore((s) => s.tasks);
  const isSearching = useGatherStore((s) => s.isSearching);
  const { activeFilter, setFilter } = useUiStore();

  const modules = getModulesByCategory(activeFilter);

  // Only show the grid when there is or was a search
  if (!isSearching && Object.keys(tasks).length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <Tabs
        value={activeFilter}
        onValueChange={(v) => setFilter(v as ModuleCategory | "all")}
      >
        <TabsList className="bg-card border border-border">
          {CATEGORIES.map((cat) => {
            const count =
              cat.value === "all"
                ? MODULE_REGISTRY.length
                : getModulesByCategory(cat.value).length;
            return (
              <TabsTrigger key={cat.value} value={cat.value}>
                {cat.label}
                <span className="ml-1 text-xs text-muted-foreground">
                  {count}
                </span>
              </TabsTrigger>
            );
          })}
        </TabsList>
      </Tabs>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(80px,1fr))] gap-2">
        {modules.map((mod) => {
          const task = tasks[mod.id];
          const Icon = getModuleIcon(mod.icon);
          return (
            <div
              key={mod.id}
              className="group flex flex-col items-center gap-1.5 rounded-lg border border-border bg-card/50 p-3 transition-colors hover:border-primary/30 hover:bg-card"
            >
              <div className="relative">
                <Icon className="size-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                <div className="absolute -right-1.5 -top-1.5">
                  <StatusIndicator status={task?.status} />
                </div>
              </div>
              <span className="max-w-full truncate text-[10px] text-muted-foreground group-hover:text-foreground/80 transition-colors">
                {mod.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
