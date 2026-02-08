"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, Check, Plus, Trash2, Key } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

type ApiKeyScope = "ingest" | "read" | "full";

interface ApiKey {
  id: string;
  prefix: string;
  name: string;
  scope: ApiKeyScope;
  created_at: string;
  revoked_at: string | null;
}

const SCOPE_LABELS: Record<ApiKeyScope, string> = {
  ingest: "Ingest only",
  read: "Read only",
  full: "Full access",
};

const SCOPE_COLORS: Record<ApiKeyScope, string> = {
  ingest: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  read: "bg-green-500/10 text-green-400 border-green-500/20",
  full: "bg-orange-500/10 text-orange-400 border-orange-500/20",
};

export function ApiKeyManager({
  teamId,
  keys,
  maxKeys,
  activeCount,
}: {
  teamId: string;
  keys: ApiKey[];
  maxKeys: number;
  activeCount: number;
}) {
  const [newKeyName, setNewKeyName] = useState("Default");
  const [newKeyScope, setNewKeyScope] = useState<ApiKeyScope>("full");
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null);
  const router = useRouter();
  const { toast } = useToast();

  async function handleCreate() {
    setLoading(true);
    const res = await fetch("/api/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newKeyName, team_id: teamId, scope: newKeyScope }),
    });

    if (!res.ok) {
      const data = await res
        .json()
        .catch(() => ({ error: "Failed to create key" }));
      toast({
        title: "Error",
        description: data.error,
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    const data = await res.json();
    setRawKey(data.raw_key);
    setLoading(false);
    toast({ title: "API key created" });
    router.refresh();
  }

  async function handleRevoke(keyId: string) {
    const res = await fetch(`/api/keys/${keyId}`, { method: "DELETE" });
    setRevokeTarget(null);
    if (!res.ok) {
      const data = await res
        .json()
        .catch(() => ({ error: "Failed to revoke key" }));
      toast({
        title: "Error",
        description: data.error,
        variant: "destructive",
      });
      return;
    }
    toast({ title: "Key revoked" });
    router.refresh();
  }

  function handleCopy() {
    if (rawKey) {
      navigator.clipboard.writeText(rawKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDialogClose(open: boolean) {
    setDialogOpen(open);
    if (!open) {
      setRawKey(null);
      setCopied(false);
      setNewKeyName("Default");
      setNewKeyScope("full");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">API Keys</h2>
          <p className="text-sm text-muted-foreground">
            {activeCount} / {maxKeys} keys used
          </p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              disabled={activeCount >= maxKeys}
              onClick={() => setDialogOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Generate key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {rawKey ? "Key created" : "Generate API key"}
              </DialogTitle>
              <DialogDescription>
                {rawKey
                  ? "Copy this key now. You won't be able to see it again."
                  : "Give your key a name to identify it later."}
              </DialogDescription>
            </DialogHeader>

            {rawKey ? (
              <div className="space-y-3">
                <div className="rounded-lg border bg-muted p-3 font-mono text-sm break-all">
                  {rawKey}
                </div>
                <Button onClick={handleCopy} className="w-full gap-2">
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" /> Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" /> Copy to clipboard
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key-name">Key name</Label>
                  <Input
                    id="key-name"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g. production, staging"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Permissions</Label>
                  <div className="grid grid-cols-3 gap-2">
                    {(["ingest", "read", "full"] as const).map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setNewKeyScope(s)}
                        className={`rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                          newKeyScope === s
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border text-muted-foreground hover:border-primary/50"
                        }`}
                      >
                        <div>{SCOPE_LABELS[s]}</div>
                        <div className="mt-0.5 font-normal text-[10px] opacity-70">
                          {s === "ingest" && "Send traces"}
                          {s === "read" && "Query data"}
                          {s === "full" && "Both"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
                <Button
                  onClick={handleCreate}
                  className="w-full"
                  disabled={loading}
                >
                  {loading ? "Generating..." : "Generate"}
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-xl border bg-card">
        {keys.length === 0 ? (
          <div className="p-8 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-muted">
              <Key className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">
              No API keys yet. Generate one to start sending traces.
            </p>
          </div>
        ) : (
          <div className="divide-y">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm font-medium">
                      {key.prefix}...
                    </span>
                    <span className="text-sm text-muted-foreground truncate">
                      {key.name}
                    </span>
                    <span className={`inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${SCOPE_COLORS[key.scope]}`}>
                      {SCOPE_LABELS[key.scope]}
                    </span>
                    {key.revoked_at && (
                      <Badge variant="secondary" className="text-xs">
                        Revoked
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Created {new Date(key.created_at).toLocaleDateString()}
                  </p>
                </div>
                {!key.revoked_at && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="shrink-0 gap-1.5 text-destructive hover:text-destructive"
                    onClick={() => setRevokeTarget(key.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog
        open={revokeTarget !== null}
        onOpenChange={(open) => {
          if (!open) setRevokeTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke API key</DialogTitle>
            <DialogDescription>
              This key will stop working immediately. Any agents using it will
              lose access. Are you sure?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRevokeTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => revokeTarget && handleRevoke(revokeTarget)}
            >
              Revoke key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
