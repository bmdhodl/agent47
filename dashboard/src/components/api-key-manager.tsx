"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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

interface ApiKey {
  id: string;
  prefix: string;
  name: string;
  created_at: string;
  revoked_at: string | null;
}

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
      body: JSON.stringify({ name: newKeyName, team_id: teamId }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({ error: "Failed to create key" }));
      toast({ title: "Error", description: data.error, variant: "destructive" });
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
      const data = await res.json().catch(() => ({ error: "Failed to revoke key" }));
      toast({ title: "Error", description: data.error, variant: "destructive" });
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
    }
  }

  return (
    <div className="space-y-4">
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
            >
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
                <div className="rounded-md border bg-muted p-3 font-mono text-sm break-all">
                  {rawKey}
                </div>
                <Button onClick={handleCopy} className="w-full">
                  {copied ? "Copied!" : "Copy to clipboard"}
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

      <div className="rounded-md border">
        {keys.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No API keys yet. Generate one to start sending traces.
          </div>
        ) : (
          <div className="divide-y">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{key.prefix}...</span>
                    <span className="text-sm text-muted-foreground">
                      {key.name}
                    </span>
                    {key.revoked_at && (
                      <Badge variant="secondary">Revoked</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Created{" "}
                    {new Date(key.created_at).toLocaleDateString()}
                  </p>
                </div>
                {!key.revoked_at && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setRevokeTarget(key.id)}
                  >
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={revokeTarget !== null} onOpenChange={(open) => { if (!open) setRevokeTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke API key</DialogTitle>
            <DialogDescription>
              This key will stop working immediately. Any agents using it will lose access. Are you sure?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRevokeTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => revokeTarget && handleRevoke(revokeTarget)}>
              Revoke key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
