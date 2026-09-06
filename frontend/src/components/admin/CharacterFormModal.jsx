import { useState } from "react";
import { UserCircle2, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import { createAdminCharacter, updateAdminCharacter } from "../../lib/api";

const CHECKPOINT_PATTERN = /^S\d+E\d+$/i;

function CharacterFormModal({
  animeId,
  factions,
  existingCharacter,
  token,
  onSaved,
  onClose,
}) {
  const isEditing = Boolean(existingCharacter);
  const [name, setName] = useState(existingCharacter?.name ?? "");
  const [role, setRole] = useState(existingCharacter?.role ?? "");
  const [height, setHeight] = useState(existingCharacter?.height ?? "");
  const [avatarUrl, setAvatarUrl] = useState(
    existingCharacter?.avatar_url ?? "",
  );
  const [bounty, setBounty] = useState(existingCharacter?.bounty ?? "");
  const [power, setPower] = useState(existingCharacter?.power ?? "");
  const [backstory, setBackstory] = useState(
    existingCharacter?.backstory ?? "",
  );
  const [factionId, setFactionId] = useState(
    existingCharacter?.faction_id != null
      ? String(existingCharacter.faction_id)
      : "",
  );
  const [firstRevealedAt, setFirstRevealedAt] = useState(
    existingCharacter?.first_revealed_at ?? "S1E1",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  const isValidCheckpoint = CHECKPOINT_PATTERN.test(firstRevealedAt.trim());

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !name.trim() || !isValidCheckpoint) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    const payload = {
      name: name.trim(),
      role: role.trim() || null,
      height: height.trim() || null,
      avatar_url: avatarUrl.trim() || null,
      bounty: bounty.trim() || null,
      power: power.trim() || null,
      backstory: backstory.trim() || null,
      faction_id: factionId ? Number(factionId) : null,
      first_revealed_at: firstRevealedAt.trim(),
    };

    try {
      if (isEditing) {
        await updateAdminCharacter(token, existingCharacter.id, payload);
      } else {
        await createAdminCharacter(token, animeId, payload);
      }
      onSaved();
    } catch (submitError) {
      setError(
        submitError.status === 422
          ? "That checkpoint is out of range for this anime's seasons."
          : "Could not save that character. Please try again.",
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
            <UserCircle2 className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              {isEditing ? "Edit Character" : "Add Character"}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close character form"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto"
        >
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
            Role
            <input
              type="text"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              placeholder="e.g. Main, Supporting"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Faction
            <select
              value={factionId}
              onChange={(event) => setFactionId(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            >
              <option value="">None</option>
              {factions.map((faction) => (
                <option key={faction.id} value={faction.id}>
                  {faction.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            First Revealed At (checkpoint)
            <input
              type="text"
              required
              value={firstRevealedAt}
              onChange={(event) => setFirstRevealedAt(event.target.value)}
              placeholder="e.g. S1E1"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Height
            <input
              type="text"
              value={height}
              onChange={(event) => setHeight(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Avatar URL
            <input
              type="text"
              value={avatarUrl}
              onChange={(event) => setAvatarUrl(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Power / Ability{" "}
            <span className="text-[var(--pink)]">(spoiler-gated)</span>
            <input
              type="text"
              value={power}
              onChange={(event) => setPower(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Bounty <span className="text-[var(--pink)]">(spoiler-gated)</span>
            <input
              type="text"
              value={bounty}
              onChange={(event) => setBounty(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Backstory{" "}
            <span className="text-[var(--pink)]">(spoiler-gated)</span>
            <textarea
              value={backstory}
              onChange={(event) => setBackstory(event.target.value)}
              rows={3}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {!isValidCheckpoint && (
            <p className="text-xs text-[var(--pink)]">
              Checkpoint must look like S1E12.
            </p>
          )}
          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !name.trim() || !isValidCheckpoint}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting
              ? "Saving..."
              : isEditing
                ? "Save Changes"
                : "Add Character"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default CharacterFormModal;
