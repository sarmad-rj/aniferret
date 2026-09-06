import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";

const CONFIRMATION_WORD = "DELETE";

function DeleteAccountModal({ onConfirm, onClose }) {
  const [password, setPassword] = useState("");
  const [confirmationText, setConfirmationText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  const canSubmit =
    password.length > 0 &&
    confirmationText === CONFIRMATION_WORD &&
    !isSubmitting;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await onConfirm(password);
    } catch {
      setError(
        "Could not delete your account. Check your password and try again.",
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-[var(--pink)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Delete Account
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close delete account"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-4 rounded-md bg-[var(--pink-light)] p-3 text-xs text-[var(--primary)]">
          This permanently deletes your account and all associated watch
          progress. This action cannot be undone.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Current password
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Type DELETE to confirm
            <input
              type="text"
              required
              value={confirmationText}
              onChange={(event) => setConfirmationText(event.target.value)}
              placeholder={CONFIRMATION_WORD}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={!canSubmit}
            className="mt-1 rounded-md bg-[var(--pink)] px-3 py-2 text-sm font-medium text-[var(--primary)] disabled:opacity-50"
          >
            {isSubmitting ? "Deleting..." : "Permanently Delete Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default DeleteAccountModal;
