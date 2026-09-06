import { useState } from "react";
import { Wrench, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import {
  fixAdminCharacterCheckpoint,
  fixAdminFactCheckpoint,
} from "../../lib/api";

const CHECKPOINT_PATTERN = /^S\d+E\d+$/i;

function FixCheckpointModal({ issue, token, onFixed, onClose }) {
  const [checkpoint, setCheckpoint] = useState(issue.checkpoint);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  const isValidFormat = CHECKPOINT_PATTERN.test(checkpoint.trim());

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !isValidFormat) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const trimmed = checkpoint.trim();
      if (issue.entity_type === "character") {
        await fixAdminCharacterCheckpoint(token, issue.entity_id, trimmed);
      } else {
        await fixAdminFactCheckpoint(
          token,
          issue.entity_id,
          issue.field,
          trimmed,
        );
      }
      onFixed();
    } catch (submitError) {
      setError(
        submitError.status === 422
          ? "That checkpoint is still out of range for this anime's seasons."
          : "Could not save that fix. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wrench className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Fix Checkpoint
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close fix checkpoint"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-1 text-xs text-[var(--text-muted)]">
          {issue.anime_title} &mdash; {issue.entity_label} ({issue.field})
        </p>
        <p className="mb-4 text-xs text-[var(--pink)]">{issue.reason}</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Corrected Checkpoint
            <input
              type="text"
              required
              value={checkpoint}
              onChange={(event) => setCheckpoint(event.target.value)}
              placeholder="e.g. S1E12"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {!isValidFormat && (
            <p className="text-xs text-[var(--pink)]">
              Expected format: S&lt;season&gt;E&lt;episode&gt;, e.g. S1E12.
            </p>
          )}
          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !isValidFormat}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting ? "Saving..." : "Save Fix"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default FixCheckpointModal;
