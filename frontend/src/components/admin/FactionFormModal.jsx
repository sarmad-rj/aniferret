import { useState } from "react";
import { Shield, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import { createAdminFaction, updateAdminFaction } from "../../lib/api";

const CHECKPOINT_PATTERN = /^S\d+E\d+$/i;

function FactionFormModal({
  animeId,
  factions,
  existingFaction,
  token,
  onSaved,
  onClose,
}) {
  const isEditing = Boolean(existingFaction);
  const [name, setName] = useState(existingFaction?.name ?? "");
  const [description, setDescription] = useState(
    existingFaction?.description ?? "",
  );
  const [parentId, setParentId] = useState(
    existingFaction?.parent_id != null ? String(existingFaction.parent_id) : "",
  );
  const [firstRevealedAt, setFirstRevealedAt] = useState(
    existingFaction?.first_revealed_at ?? "",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  // Only top-level factions (no parent of their own) can be chosen as a parent --
  // this app's faction hierarchy is strictly two-tier -- and a faction can't be
  // its own parent when editing.
  const parentOptions = factions.filter(
    (faction) =>
      faction.parent_id == null && faction.id !== existingFaction?.id,
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !name.trim()) {
      return;
    }
    if (
      firstRevealedAt.trim() &&
      !CHECKPOINT_PATTERN.test(firstRevealedAt.trim())
    ) {
      setError("Checkpoint must look like S1E12, or leave it blank.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    const payload = {
      name: name.trim(),
      description: description.trim() || null,
      parent_id: parentId ? Number(parentId) : null,
      first_revealed_at: firstRevealedAt.trim() || null,
    };

    try {
      if (isEditing) {
        await updateAdminFaction(token, existingFaction.id, payload);
      } else {
        await createAdminFaction(token, animeId, payload);
      }
      onSaved();
    } catch {
      setError("Could not save that faction. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              {isEditing ? "Edit Faction" : "Add Faction"}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close faction form"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Name
            <input
              type="text"
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={2}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Parent Faction (optional)
            <select
              value={parentId}
              onChange={(event) => setParentId(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            >
              <option value="">None (top-level)</option>
              {parentOptions.map((faction) => (
                <option key={faction.id} value={faction.id}>
                  {faction.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            First Revealed At (optional checkpoint)
            <input
              type="text"
              value={firstRevealedAt}
              onChange={(event) => setFirstRevealedAt(event.target.value)}
              placeholder="e.g. S1E1"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !name.trim()}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting
              ? "Saving..."
              : isEditing
                ? "Save Changes"
                : "Add Faction"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default FactionFormModal;
