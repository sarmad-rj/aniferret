import { useState } from "react";
import { Plus, Trash2, Users, X } from "lucide-react";
import { postGroupSessionEvaluate } from "../lib/api";
import { formatCheckpointLabel } from "../lib/checkpoint";

function GroupModeModal({ checkpointSequence, onApply, onClose }) {
  const [watcherCheckpoints, setWatcherCheckpoints] = useState([
    checkpointSequence[0],
    checkpointSequence[0],
  ]);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleWatcherChange = (index, value) => {
    setWatcherCheckpoints((previous) =>
      previous.map((checkpoint, i) => (i === index ? value : checkpoint)),
    );
  };

  const handleAddWatcher = () => {
    setWatcherCheckpoints((previous) => [...previous, checkpointSequence[0]]);
  };

  const handleRemoveWatcher = (index) => {
    setWatcherCheckpoints((previous) => previous.filter((_, i) => i !== index));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await postGroupSessionEvaluate(watcherCheckpoints);
      onApply(response.effective_checkpoint);
    } catch {
      setError("Could not evaluate the group session. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Group Mode
            </h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close group mode">
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-4 text-xs text-[var(--text-muted)]">
          Add each co-watcher&apos;s progress. The dossier and Lore Assistant
          will lock to the lowest checkpoint, so nobody sees a spoiler ahead of
          the group.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {watcherCheckpoints.map((checkpoint, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <div key={index} className="flex items-center gap-2">
              <label className="w-20 shrink-0 text-xs text-[var(--text-muted)]">
                Watcher {index + 1}
              </label>
              <select
                value={checkpoint}
                onChange={(event) =>
                  handleWatcherChange(index, event.target.value)
                }
                className="flex-1 rounded-md border border-[var(--border)] px-2 py-1.5 text-sm text-[var(--text)]"
              >
                {checkpointSequence.map((option) => (
                  <option key={option} value={option}>
                    {formatCheckpointLabel(option)}
                  </option>
                ))}
              </select>
              {watcherCheckpoints.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveWatcher(index)}
                  aria-label={`Remove watcher ${index + 1}`}
                >
                  <Trash2 className="h-4 w-4 text-[var(--text-muted)]" />
                </button>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={handleAddWatcher}
            className="inline-flex items-center gap-1 self-start text-xs font-medium text-[var(--primary)]"
          >
            <Plus className="h-3.5 w-3.5" />
            Add co-watcher
          </button>

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting ? "Evaluating..." : "Lock to Group Checkpoint"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default GroupModeModal;
