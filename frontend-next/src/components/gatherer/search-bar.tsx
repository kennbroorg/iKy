import { type FormEvent, useState } from "react";

import { Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useModuleDispatch } from "@/hooks/use-module-query";
import { MODULE_REGISTRY } from "@/lib/module-registry";
import { useGatherStore } from "@/stores/gather-store";

const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

export function SearchBar() {
  const [value, setValue] = useState("");
  const { startSearch, isSearching } = useGatherStore();
  const { dispatch } = useModuleDispatch();

  const trimmed = value.trim();
  const detectedType = isEmail(trimmed) ? "email" : "username";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!trimmed || isSearching) return;

    startSearch(trimmed);

    if (detectedType === "email") {
      const usernamePart = trimmed.split("@")[0];

      // Dispatch email modules with full email
      const emailModules = MODULE_REGISTRY.filter(
        (m) => m.inputType === "email" || m.inputType === "both",
      );
      for (const mod of emailModules) {
        dispatch(mod.id, {
          username: trimmed,
          from: "Initial",
          ...mod.specialParams,
        });
      }

      // Dispatch username modules with username part
      const usernameModules = MODULE_REGISTRY.filter(
        (m) => m.inputType === "username",
      );
      for (const mod of usernameModules) {
        dispatch(mod.id, {
          username: usernamePart,
          from: "Initial",
          ...mod.specialParams,
        });
      }
    } else {
      // Dispatch username modules with the username
      const usernameModules = MODULE_REGISTRY.filter(
        (m) => m.inputType === "username" || m.inputType === "both",
      );
      for (const mod of usernameModules) {
        dispatch(mod.id, {
          username: trimmed,
          from: "Initial",
          ...mod.specialParams,
        });
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <div className="relative flex-1">
        <Input
          type="text"
          placeholder="Enter email or username..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="h-11 bg-card border-border pr-24 font-mono text-sm placeholder:font-sans focus-visible:border-primary focus-visible:ring-primary/30"
        />
        {trimmed && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {detectedType === "email" ? (
              <Badge className="bg-blue-600/20 text-blue-400 border-blue-500/30">
                email
              </Badge>
            ) : (
              <Badge className="bg-purple-600/20 text-purple-400 border-purple-500/30">
                username
              </Badge>
            )}
          </div>
        )}
      </div>
      <Button
        type="submit"
        disabled={!trimmed || isSearching}
        className="h-11 px-6 gap-2"
      >
        <Search className="size-4" />
        Search
      </Button>
    </form>
  );
}
