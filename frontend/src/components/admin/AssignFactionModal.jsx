import { useEffect, useState } from "react";
import { Loader2, Wrench, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import {
  fetchAdminAnimeFactions,
  fixAdminCharacterFaction,
} from "../../lib/api";

function AssignFactionModal({ entry, token, onFixed, onClose }) {
  const [factions, setFactions] = useState([]);
  const [isLoadingFactions, setIsLoadingFactions] = useState(true);
  const [selectedFactionId, setSelectedFactionId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  useEffect(() => {
    let isMounted = true;
    fetchAdminAnimeFactions(token, entry.anime_id)
      .then((data) => {
        if (isMounted) {
          setFactions(data);
          if (data.length > 0) {
            setSelectedFactionId(String(data[0].id));
          }
        }
      })
      .catch(() => {
        if (isMounted) {
          setError("Could not load factions for this anime.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingFactions(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [token, entry.anime_id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !selectedFactionId) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await fixAdminCharacterFaction(
        token,
        entry.character_id,
        Number(selectedFactionId),
      );
      onFixed();
    } catch {
      setError("Could not save that fix. Please try again.");
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
              Assign Faction
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close assign faction"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-4 text-xs text-[var(--text-muted)]">
          {entry.anime_title} &mdash; {entry.character_name}
        </p>

        {isLoadingFactions ? (
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Loading factions...
          </div>
        ) : factions.length === 0 ? (
          <p className="text-xs text-[var(--pink)]">
            This anime has no factions yet, so there&apos;s nothing to assign.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
              Faction
              <select
                value={selectedFactionId}
                onChange={(event) => setSelectedFactionId(event.target.value)}
                disabled={isSubmitting}
                className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
              >
                {factions.map((faction) => (
                  <option key={faction.id} value={faction.id}>
                    {faction.name}
                  </option>
                ))}
              </select>
            </label>

            {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
            >
              {isSubmitting ? "Saving..." : "Save Fix"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default AssignFactionModal;
