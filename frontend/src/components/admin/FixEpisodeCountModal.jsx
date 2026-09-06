import { useState } from "react";
import { Wrench, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import { fixAdminAnimeEpisodeCounts } from "../../lib/api";

function parseSeasonCounts(text) {
  return text
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
    .map((part) => Number(part));
}

function FixEpisodeCountModal({ mismatch, token, onFixed, onClose }) {
  const [totalEpisodes, setTotalEpisodes] = useState(
    String(mismatch.declared_total_episodes),
  );
  const [seasonCountsText, setSeasonCountsText] = useState(
    mismatch.season_episode_counts.join(", "),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  const parsedSeasonCounts = parseSeasonCounts(seasonCountsText);
  const isValidSeasonCounts =
    parsedSeasonCounts.length > 0 &&
    parsedSeasonCounts.every((n) => Number.isInteger(n) && n > 0);
  const parsedTotal = Number(totalEpisodes);
  const seasonCountsSum = parsedSeasonCounts.reduce((sum, n) => sum + n, 0);
  const stillMismatched =
    isValidSeasonCounts && seasonCountsSum !== parsedTotal;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !isValidSeasonCounts || stillMismatched) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await fixAdminAnimeEpisodeCounts(
        token,
        mismatch.anime_id,
        parsedTotal,
        parsedSeasonCounts,
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
              Fix Episode Counts
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close fix episode counts"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-4 text-xs text-[var(--text-muted)]">
          {mismatch.anime_title}: season episode counts sum to{" "}
          {mismatch.season_counts_sum}, but total_episodes is declared as{" "}
          {mismatch.declared_total_episodes}. Correct whichever value is wrong.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Season Episode Counts (comma-separated)
            <input
              type="text"
              required
              value={seasonCountsText}
              onChange={(event) => setSeasonCountsText(event.target.value)}
              placeholder="12, 13, 12"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Total Episodes
            <input
              type="number"
              required
              min={1}
              value={totalEpisodes}
              onChange={(event) => setTotalEpisodes(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {!isValidSeasonCounts && (
            <p className="text-xs text-[var(--pink)]">
              Enter one or more positive whole numbers, separated by commas.
            </p>
          )}
          {isValidSeasonCounts && stillMismatched && (
            <p className="text-xs text-[var(--pink)]">
              These still don&apos;t match: {seasonCountsSum} &ne;{" "}
              {parsedTotal || 0}.
            </p>
          )}
          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !isValidSeasonCounts || stillMismatched}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting ? "Saving..." : "Save Fix"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default FixEpisodeCountModal;
