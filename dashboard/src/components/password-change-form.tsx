"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-medium">Change Password</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="current-password" className="text-sm font-medium">
            Current Password
          </label>
          <Input
            id="current-password"
            type="password"
            className="max-w-sm"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            disabled={loading}
          />
          {errors.currentPassword && (
            <p className="text-sm text-destructive">{errors.currentPassword}</p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="new-password" className="text-sm font-medium">
            New Password
          </label>
          <Input
            id="new-password"
            type="password"
            className="max-w-sm"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={loading}
          />
          {errors.newPassword && (
            <p className="text-sm text-destructive">{errors.newPassword}</p>
          )}
        </div>

        <div className="space-y-1">
          <label htmlFor="confirm-password" className="text-sm font-medium">
            Confirm New Password
          </label>
          <Input
            id="confirm-password"
            type="password"
            className="max-w-sm"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
          />
          {errors.confirmPassword && (
            <p className="text-sm text-destructive">
              {errors.confirmPassword}
            </p>
          )}
        </div>

        <Button type="submit" disabled={loading}>
          {loading ? "Updating..." : "Update Password"}
        </Button>
      </form>
    </div>
  );
}
