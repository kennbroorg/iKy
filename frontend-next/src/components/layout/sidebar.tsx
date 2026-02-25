import { NavLink } from "react-router";
import {
  Search,
  User,
  Clock,
  Key,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";

const navItems = [
  { to: "/gatherer", label: "Gatherer", icon: Search },
  { to: "/profile", label: "Profile", icon: User },
  { to: "/timeline", label: "Timeline", icon: Clock },
  { to: "/apikeys", label: "API Keys", icon: Key },
] as const;

export function Sidebar() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border bg-card transition-all duration-300 ease-in-out",
        sidebarOpen ? "w-60" : "w-16",
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-14 shrink-0 items-center border-b border-border px-4",
          sidebarOpen ? "justify-start" : "justify-center",
        )}
      >
        <span
          className={cn(
            "font-mono font-bold text-primary select-none",
            "drop-shadow-[0_0_8px_var(--primary)]",
            sidebarOpen ? "text-xl" : "text-lg",
          )}
        >
          {sidebarOpen ? "iKy" : "iK"}
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all duration-200",
                sidebarOpen ? "justify-start" : "justify-center",
                isActive
                  ? "bg-primary/15 text-primary shadow-[inset_0_0_12px_-4px_var(--primary)]"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={cn(
                    "shrink-0 transition-all duration-200",
                    sidebarOpen ? "h-5 w-5" : "h-5 w-5",
                    isActive
                      ? "text-primary drop-shadow-[0_0_6px_var(--primary)]"
                      : "text-muted-foreground group-hover:text-foreground",
                  )}
                />
                {sidebarOpen && (
                  <span className="truncate transition-opacity duration-200">
                    {label}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="shrink-0 border-t border-border p-2">
        <button
          type="button"
          onClick={toggleSidebar}
          className={cn(
            "flex w-full items-center rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors duration-200",
            "hover:bg-muted/50 hover:text-foreground",
            sidebarOpen ? "justify-between" : "justify-center",
          )}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen && <span className="text-xs">Collapse</span>}
          {sidebarOpen ? (
            <ChevronsLeft className="h-4 w-4" />
          ) : (
            <ChevronsRight className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
