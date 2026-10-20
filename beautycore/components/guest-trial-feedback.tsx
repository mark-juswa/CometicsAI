"use client";

import Link from "next/link";
import { useEffect, useId, useRef } from "react";
import { LockKeyhole, CircleCheck } from "lucide-react";

export type TrialFeedbackState =
  "checking" | "available" | "processing" | "used" | "unresolved";

const messages: Record<
  TrialFeedbackState,
  { title: string; description: string }
> = {
  checking: {
    title: "Checking your trial",
    description: "Restoring your trial allowance and any existing preview.",
  },
  available: {
    title: "1 free preview available",
    description: "Choose one recommendation to generate with your guest trial.",
  },
  processing: {
    title: "Your trial preview is in progress",
    description:
      "Your one preview is being created. No additional preview will start.",
  },
  used: {
    title: "Free trial used",
    description:
      "0 of 1 previews remaining. Sign up or log in to generate more looks.",
  },
  unresolved: {
    title: "Trial request unresolved",
    description:
      "Check your existing request before continuing. A new preview will not be started.",
  },
};

export function GuestTrialIndicator({
  state,
  onOpen,
}: {
  state: TrialFeedbackState;
  onOpen: () => void;
}) {
  const message = messages[state];
  return (
    <aside
      className={"consult-trial-indicator consult-trial-" + state}
      aria-label="Guest trial allowance"
    >
      <span className="consult-trial-indicator-icon" aria-hidden="true">
        {state === "used" || state === "unresolved" ? (
          <LockKeyhole size={20} />
        ) : state === "available" ? (
          <CircleCheck size={20} />
        ) : (
          <span className="consult-spinner" />
        )}
      </span>
      <div
        className="consult-trial-indicator-copy"
        role="status"
        aria-live="polite"
      >
        <strong>{message.title}</strong>
        <p>{message.description}</p>
      </div>
      {(state === "used" || state === "unresolved") && (
        <button
          type="button"
          className="studio-secondary-button"
          onClick={onOpen}
        >
          {state === "used" ? "Unlock more previews" : "View trial details"}
        </button>
      )}
    </aside>
  );
}

export function GuestTrialLimitDialog({
  state,
  open,
  hasPreview,
  onClose,
}: {
  state: TrialFeedbackState;
  open: boolean;
  hasPreview: boolean;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    else if (!open && dialog.open) dialog.close();
    if (open) {
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = previousOverflow;
      };
    }
  }, [open]);
  const used = state === "used";
  return (
    <dialog
      ref={ref}
      className="consult-trial-dialog"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      onCancel={onClose}
      onClose={onClose}
    >
      <div className="consult-trial-dialog-content">
        <span className="consult-trial-dialog-icon" aria-hidden="true">
          <LockKeyhole size={28} />
        </span>
        <p className="studio-eyebrow">
          {used ? "GUEST TRIAL COMPLETE" : "YOUR CURRENT TRIAL"}
        </p>
        <h2 id={titleId} tabIndex={-1} autoFocus>
          {used
            ? "Your free trial has been used"
            : "Check your current trial request"}
        </h2>
        <p id={descriptionId}>
          {used
            ? "Your one guest generation attempt has been used. Create an account or log in to generate more looks, save your favorites, and book a service."
            : "Your trial request may still be running or its status is uncertain. Check the existing request before continuing. No replacement image will be started."}
        </p>
        {used && (
          <p className="consult-trial-dialog-count">
            0 of 1 previews remaining
          </p>
        )}
        {hasPreview && (
          <p>You can keep browsing and download your generated preview.</p>
        )}
        <div className="consult-trial-dialog-actions">
          <Link
            className="studio-primary-button"
            href="/register?continue=consultation"
          >
            Create account
          </Link>
          <Link
            className="studio-secondary-button"
            href="/login?continue=consultation"
          >
            Log in
          </Link>
        </div>
        <p className="consult-trial-dialog-note">
          Signing up starts a fresh consultation. Your guest preview is not
          automatically saved or transferred.
        </p>
        <button
          type="button"
          className="studio-text-button consult-trial-dialog-dismiss"
          onClick={onClose}
        >
          Keep browsing
        </button>
      </div>
    </dialog>
  );
}
