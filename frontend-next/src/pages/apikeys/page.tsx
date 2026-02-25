import { useCallback, useEffect, useRef, useState } from "react";

import {
  Check,
  Download,
  Eye,
  EyeOff,
  Key,
  Loader2,
  Pencil,
  Plus,
  Save,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useApiKeys } from "@/hooks/use-api-keys";
import { useApiKeyStore } from "@/stores/apikey-store";
import type { ApiKey } from "@/types/api";

/* ---------- helpers ---------- */

function generateId(): string {
  return crypto.randomUUID();
}

function maskKey(key: string): string {
  if (key.length <= 4) return key;
  return `${key.slice(0, 4)}${"*".repeat(Math.min(key.length - 4, 16))}`;
}

function isValidApiKeyArray(data: unknown): data is ApiKey[] {
  if (!Array.isArray(data)) return false;
  return data.every(
    (item) =>
      typeof item === "object" &&
      item !== null &&
      "name" in item &&
      "key" in item &&
      typeof item.name === "string" &&
      typeof item.key === "string",
  );
}

/* ---------- row component ---------- */

interface KeyRowProps {
  apiKey: ApiKey;
  isEditing: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: (name: string, key: string) => void;
  onDelete: () => void;
}

function KeyRow({
  apiKey,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onDelete,
}: KeyRowProps) {
  const [name, setName] = useState(apiKey.name);
  const [key, setKey] = useState(apiKey.key);
  const [revealed, setRevealed] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);

  // Sync local state when switching to edit mode
  useEffect(() => {
    if (isEditing) {
      setName(apiKey.name);
      setKey(apiKey.key);
      // Auto-focus name input in edit mode
      setTimeout(() => nameRef.current?.focus(), 50);
    }
  }, [isEditing, apiKey.name, apiKey.key]);

  const handleSave = () => {
    if (!name.trim()) {
      toast.error("Name is required");
      return;
    }
    onSaveEdit(name.trim(), key);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") onCancelEdit();
  };

  return (
    <>
      <TableRow className="border-border/50 hover:bg-muted/20 transition-colors">
        {/* Name column */}
        <TableCell className="font-medium">
          {isEditing ? (
            <Input
              ref={nameRef}
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="API key name..."
              className="h-8 bg-background/50 border-border"
            />
          ) : (
            <span className="text-foreground">{apiKey.name}</span>
          )}
        </TableCell>

        {/* Key column */}
        <TableCell className="font-mono text-sm">
          {isEditing ? (
            <div className="flex items-center gap-2">
              <Input
                type={revealed ? "text" : "password"}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter API key..."
                className="h-8 bg-background/50 border-border font-mono"
              />
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => setRevealed(!revealed)}
                title={revealed ? "Hide key" : "Reveal key"}
              >
                {revealed ? (
                  <EyeOff className="size-3.5 text-muted-foreground" />
                ) : (
                  <Eye className="size-3.5 text-muted-foreground" />
                )}
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">
                {revealed ? apiKey.key : maskKey(apiKey.key)}
              </span>
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => setRevealed(!revealed)}
                title={revealed ? "Hide key" : "Reveal key"}
              >
                {revealed ? (
                  <EyeOff className="size-3.5 text-muted-foreground" />
                ) : (
                  <Eye className="size-3.5 text-muted-foreground" />
                )}
              </Button>
            </div>
          )}
        </TableCell>

        {/* Actions column */}
        <TableCell className="text-right">
          {isEditing ? (
            <div className="flex items-center justify-end gap-1">
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={handleSave}
                title="Confirm edit"
                className="text-green-400 hover:text-green-300 hover:bg-green-400/10"
              >
                <Check className="size-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={onCancelEdit}
                title="Cancel edit"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-3.5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-end gap-1">
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={onStartEdit}
                title="Edit key"
                className="text-muted-foreground hover:text-primary"
              >
                <Pencil className="size-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => setShowDeleteDialog(true)}
                title="Delete key"
                className="text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-3.5" />
              </Button>
            </div>
          )}
        </TableCell>
      </TableRow>

      {/* Delete confirmation dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete API Key</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the key{" "}
              <span className="font-semibold text-foreground">
                {apiKey.name || "Untitled"}
              </span>
              ? This change takes effect when you save.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button
              variant="destructive"
              onClick={() => {
                onDelete();
                setShowDeleteDialog(false);
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/* ---------- main page ---------- */

export default function ApiKeysPage() {
  const { query, save, isSaving } = useApiKeys();
  const { keys, addKey, updateKey, removeKey } = useApiKeyStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Track whether local state has diverged from server state
  const [isDirty, setIsDirty] = useState(false);

  const handleAddKey = useCallback(() => {
    const newKey: ApiKey = { id: generateId(), name: "", key: "" };
    addKey(newKey);
    setEditingId(newKey.id);
    setIsDirty(true);
  }, [addKey]);

  const handleSaveEdit = useCallback(
    (id: string, name: string, key: string) => {
      updateKey(id, { name, key });
      setEditingId(null);
      setIsDirty(true);
    },
    [updateKey],
  );

  const handleCancelEdit = useCallback(
    (apiKey: ApiKey) => {
      // If the key was freshly added and has no name/key, remove it
      if (!apiKey.name && !apiKey.key) {
        removeKey(apiKey.id);
      }
      setEditingId(null);
    },
    [removeKey],
  );

  const handleDelete = useCallback(
    (id: string) => {
      removeKey(id);
      if (editingId === id) setEditingId(null);
      setIsDirty(true);
    },
    [removeKey, editingId],
  );

  const handleSaveAll = useCallback(() => {
    save(keys, {
      onSuccess: () => {
        toast.success("API keys saved successfully");
        setIsDirty(false);
      },
      onError: (error) => {
        toast.error(`Failed to save: ${error.message}`);
      },
    });
  }, [save, keys]);

  /* --- Import JSON --- */
  const handleImport = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsed: unknown = JSON.parse(e.target?.result as string);

          // Accept either { keys: [...] } or bare [...]
          let keyArray: unknown;
          if (
            typeof parsed === "object" &&
            parsed !== null &&
            "keys" in parsed
          ) {
            keyArray = (parsed as { keys: unknown }).keys;
          } else {
            keyArray = parsed;
          }

          if (!isValidApiKeyArray(keyArray)) {
            toast.error(
              'Invalid JSON format. Expected an array of { name, key } objects or { keys: [...] }.',
            );
            return;
          }

          // Assign IDs if missing and merge into store
          const withIds = keyArray.map((k) => ({
            id: k.id || generateId(),
            name: k.name,
            key: k.key,
          }));

          // Replace all keys
          const { setKeys } = useApiKeyStore.getState();
          setKeys(withIds);
          setIsDirty(true);
          toast.success(`Imported ${withIds.length} key(s)`);
        } catch {
          toast.error("Failed to parse JSON file");
        }
      };
      reader.readAsText(file);

      // Reset file input so the same file can be re-imported
      event.target.value = "";
    },
    [],
  );

  /* --- Export JSON --- */
  const handleExport = useCallback(() => {
    const data = JSON.stringify({ keys }, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "iky-apikeys.json";
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Exported API keys");
  }, [keys]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-primary">
            <Key className="size-6" />
            API Keys
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage API keys for OSINT modules that require authentication.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Hidden file input for import */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={handleImport}
          />

          <Button
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="gap-1.5 border-border"
          >
            <Upload className="size-3.5" />
            Import
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={keys.length === 0}
            className="gap-1.5 border-border"
          >
            <Download className="size-3.5" />
            Export
          </Button>

          <Button
            size="sm"
            onClick={handleSaveAll}
            disabled={isSaving || !isDirty}
            className="gap-1.5"
          >
            {isSaving ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Save className="size-3.5" />
            )}
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      {/* Content card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configured Keys</CardTitle>
          <CardDescription>
            {keys.length === 0
              ? "No keys configured yet."
              : `${keys.length} key${keys.length === 1 ? "" : "s"} configured`}
            {isDirty && (
              <span className="ml-2 text-yellow-400">(unsaved changes)</span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Loading state */}
          {query.isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading API keys...
              </span>
            </div>
          )}

          {/* Error state */}
          {query.isError && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
              Failed to load API keys: {query.error.message}
            </div>
          )}

          {/* Empty state */}
          {!query.isLoading && !query.isError && keys.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border py-12">
              <Key className="size-10 text-muted-foreground/50" />
              <div className="text-center">
                <p className="text-sm font-medium text-muted-foreground">
                  No API keys configured
                </p>
                <p className="mt-1 text-xs text-muted-foreground/70">
                  Add a key or import from JSON to get started.
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="gap-1.5"
                >
                  <Upload className="size-3.5" />
                  Import JSON
                </Button>
                <Button size="sm" onClick={handleAddKey} className="gap-1.5">
                  <Plus className="size-3.5" />
                  Add Key
                </Button>
              </div>
            </div>
          )}

          {/* Table */}
          {!query.isLoading && keys.length > 0 && (
            <div className="space-y-3">
              <div className="rounded-md border border-border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border bg-muted/30 hover:bg-muted/30">
                      <TableHead className="text-xs font-medium uppercase tracking-wide text-muted-foreground w-[30%]">
                        Name
                      </TableHead>
                      <TableHead className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Key
                      </TableHead>
                      <TableHead className="text-xs font-medium uppercase tracking-wide text-muted-foreground text-right w-[100px]">
                        Actions
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {keys.map((apiKey) => (
                      <KeyRow
                        key={apiKey.id}
                        apiKey={apiKey}
                        isEditing={editingId === apiKey.id}
                        onStartEdit={() => setEditingId(apiKey.id)}
                        onCancelEdit={() => handleCancelEdit(apiKey)}
                        onSaveEdit={(name, key) =>
                          handleSaveEdit(apiKey.id, name, key)
                        }
                        onDelete={() => handleDelete(apiKey.id)}
                      />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Add key button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddKey}
                disabled={editingId !== null}
                className="gap-1.5 border-dashed border-border text-muted-foreground hover:text-foreground"
              >
                <Plus className="size-3.5" />
                Add Key
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
