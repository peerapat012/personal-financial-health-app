import { useEffect, useRef, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Inbox, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <div className="feedback-state" role="status"><LoaderCircle className="spin" /><p>{label}</p></div>;
}

export function EmptyState({ title, description, icon: Icon = Inbox, action }: {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: ReactNode;
}) {
  return <section className="feedback-state feedback-empty"><Icon /><h3>{title}</h3><p>{description}</p>{action}</section>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <section className="feedback-state" role="alert"><AlertTriangle /><h3>Something went wrong</h3><p>{message}</p>{onRetry && <Button onClick={onRetry}>Try again</Button>}</section>;
}

export function ConfirmationDialog({ open, title, description, confirmLabel = "Confirm", onConfirm, onCancel }: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} className="confirm-dialog" onCancel={onCancel} onClose={onCancel}>
      <h2>{title}</h2>
      <p>{description}</p>
      <div>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button variant="destructive" onClick={onConfirm}>{confirmLabel}</Button>
      </div>
    </dialog>
  );
}

export function UnsavedFormFeedback({ open, onDiscard, onKeepEditing }: {
  open: boolean;
  onDiscard: () => void;
  onKeepEditing: () => void;
}) {
  return <ConfirmationDialog open={open} title="Discard unsaved changes?" description="Your entries on this form will be lost." confirmLabel="Discard changes" onConfirm={onDiscard} onCancel={onKeepEditing} />;
}
