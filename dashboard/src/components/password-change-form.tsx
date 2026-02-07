"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

export function PasswordChangeForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const { toast } = useToast();

  function validate(): boolean {
    const next: typeof errors = {};

    if (!currentPassword) {
      next.currentPassword = "Current password is required";
    }

    if (!newPassword) {
      next.newPassword = "New password is required";
    } else if (newPassword.length < 6) {
      next.newPassword = "Password must be at least 6 characters";
    }

    if (!confirmPassword) {
      next.confirmPassword = "Please confirm your new password";
    } else if (newPassword !== confirmPassword) {
      next.confirmPassword = "Passwords do not match";
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!validate()) return;

    setLoading(true);
    setErrors({});

    try {
      const res = await fetch("/api/user/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ currentPassword, newPassword }),
      });

      if (!res.ok) {
        const data = await res
          .json()
          .catch(() => ({ error: "Failed to change password" }));
        toast({
          title: "Error",
          description: data.error,
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      toast({
        title: "Password updated",
        description: "Your password has been changed successfully.",
      });

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  const fields = [
    {
      id: "current-password",
      label: "Current Password",
      value: currentPassword,
      onChange: setCurrentPassword,
      error: errors.currentPassword,
      autoComplete: "current-password",
    },
    {
      id: "new-password",
      label: "New Password",
      value: newPassword,
      onChange: setNewPassword,
      error: errors.newPassword,
      autoComplete: "new-password",
    },
    {
      id: "confirm-password",
      label: "Confirm New Password",
      value: confirmPassword,
      onChange: setConfirmPassword,
      error: errors.confirmPassword,
      autoComplete: "new-password",
    },
  ];

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-medium">Change Password</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((field) => (
          <div key={field.id} className="space-y-1.5">
            <Label htmlFor={field.id}>{field.label}</Label>
            <Input
              id={field.id}
              type="password"
              className="max-w-sm"
              value={field.value}
              onChange={(e) => field.onChange(e.target.value)}
              disabled={loading}
              autoComplete={field.autoComplete}
            />
            {field.error && (
              <p className="text-sm text-destructive">{field.error}</p>
            )}
          </div>
        ))}

        <Button type="submit" disabled={loading}>
          {loading ? "Updating..." : "Update Password"}
        </Button>
      </form>
    </section>
  );
}
