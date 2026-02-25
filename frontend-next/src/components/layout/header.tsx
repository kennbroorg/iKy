import { PanelLeft, PanelLeftClose } from "lucide-react";

import { useUiStore } from "@/stores/ui-store";

export function Header() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <header className="flex h-14 shrink-0 items-center border-b border-border bg-background px-4">
      {/* Sidebar toggle */}
      <button
        type="button"
        onClick={toggleSidebar}
        className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
        aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
      >
        {sidebarOpen ? (
          <PanelLeftClose className="h-5 w-5" />
        ) : (
          <PanelLeft className="h-5 w-5" />
        )}
      </button>

      {/* Branding */}
      <div className="flex flex-1 items-center justify-end pr-2">
        <span className="font-mono text-sm font-medium text-primary drop-shadow-[0_0_6px_var(--primary)]">
          iKy
        </span>
      </div>
    </header>
  );
}
