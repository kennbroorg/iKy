import { Download } from "lucide-react";

import { ModuleGrid } from "@/components/gatherer/module-grid";
import { ResultCard } from "@/components/gatherer/result-card";
import { SearchBar } from "@/components/gatherer/search-bar";
import { Button } from "@/components/ui/button";
import { useGatherStore } from "@/stores/gather-store";

function ExportButton() {
  const tasks = useGatherStore((s) => s.tasks);

  function handleExport() {
    const results: Record<string, unknown> = {};
    for (const [moduleId, task] of Object.entries(tasks)) {
      if (task.status === "success" && task.result) {
        results[moduleId] = task.result;
      }
    }

    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `iky-results-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
      <Download className="size-4" />
      Export JSON
    </Button>
  );
}

export default function GathererPage() {
  const tasks = useGatherStore((s) => s.tasks);
  const completedModules = Object.entries(tasks).filter(
    ([, t]) => t.status === "success" && t.result,
  );

  return (
    <div className="space-y-6">
      <SearchBar />
      <ModuleGrid />
      {completedModules.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Results</h2>
            <ExportButton />
          </div>
          {completedModules.map(([moduleId, task]) => (
            <ResultCard key={moduleId} moduleId={moduleId} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
