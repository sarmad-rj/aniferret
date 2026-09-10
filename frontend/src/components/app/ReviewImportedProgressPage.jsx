import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import { ArrowLeft, CheckCircle2, Film, Loader2 } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import ProgressSlider from "../ProgressSlider";
import { checkpointFromCumulativeEpisodes } from "../../lib/checkpoint";
import { saveWatchProgress } from "../../lib/api";

function buildInitialCheckpoints(entries, animeBySlug) {
  const checkpoints = {};
  for (const entry of entries) {
    const anime = animeBySlug[entry.anime_slug];
    const checkpoint = checkpointFromCumulativeEpisodes(
      anime?.season_episode_counts,
      entry.watched_episodes,
    );
    if (checkpoint) {
      checkpoints[entry.anime_slug] = checkpoint;
    }
  }
  return checkpoints;
}

function ReviewImportedProgressPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { animeList } = useOutletContext();
  const { token } = useAuth();

  const skippedEntries = location.state?.skippedEntries ?? [];
  const animeBySlug = Object.fromEntries(
    animeList.map((anime) => [anime.slug, anime]),
  );
  const entriesWithAnime = skippedEntries.filter(
    (entry) => animeBySlug[entry.anime_slug],
  );

  const [checkpoints, setCheckpoints] = useState(() =>
    buildInitialCheckpoints(entriesWithAnime, animeBySlug),
  );
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [isSaved, setIsSaved] = useState(false);

  const handleCheckpointChange = (slug, newCheckpoint) => {
    setCheckpoints((previous) => ({ ...previous, [slug]: newCheckpoint }));
  };

  const handleSaveAll = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      await saveWatchProgress(
        token,
        entriesWithAnime.map((entry) => ({
          anime_slug: entry.anime_slug,
          checkpoint: checkpoints[entry.anime_slug],
        })),
      );
      setIsSaved(true);
    } catch {
      setSaveError("Could not save your progress. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  if (entriesWithAnime.length === 0) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-10 text-center sm:px-6">
        <p className="text-sm text-[var(--text-muted)]">
          Nothing to review right now — import a MyAnimeList export to set up
          multi-season shows here.
        </p>
        <Link
          to="/app/discover"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-[var(--primary)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Discover
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <button
        type="button"
        onClick={() => navigate("/app/discover")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-[var(--primary)]"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <h1 className="mb-2 text-xl font-bold text-[var(--primary)]">
        Set Up Watch Progress
      </h1>
      <p className="mb-6 text-xs text-[var(--text-muted)]">
        These are multi-season shows your MyAnimeList import couldn't set
        automatically — one MAL entry can't tell us which season you're actually
        on. Each slider is pre-filled from your MAL progress as a starting
        point, not a confirmed answer — double-check it, adjust if it's off,
        then Save All.
      </p>

      <div className="flex flex-col gap-4">
        {entriesWithAnime.map((entry) => {
          const anime = animeBySlug[entry.anime_slug];
          const checkpoint = checkpoints[entry.anime_slug];

          return (
            <div
              key={entry.anime_slug}
              className="flex flex-col gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 sm:flex-row sm:items-start"
            >
              <div className="flex shrink-0 items-center gap-3 sm:w-32 sm:flex-col sm:items-start">
                {anime.cover_image_url ? (
                  <img
                    src={anime.cover_image_url}
                    alt={anime.title}
                    className="aspect-[2/3] w-20 shrink-0 rounded-md object-cover sm:w-32"
                  />
                ) : (
                  <div className="flex aspect-[2/3] w-20 shrink-0 items-center justify-center rounded-md bg-[var(--surface-warm)] sm:w-32">
                    <Film className="h-6 w-6 text-[var(--ferret)]" />
                  </div>
                )}
                <h2 className="text-sm font-semibold text-[var(--text)]">
                  {anime.title}
                </h2>
              </div>

              <div className="min-w-0 flex-1">
                <ProgressSlider
                  anime={anime}
                  checkpoint={checkpoint}
                  onCheckpointChange={(newCheckpoint) =>
                    handleCheckpointChange(entry.anime_slug, newCheckpoint)
                  }
                />
              </div>
            </div>
          );
        })}
      </div>

      {saveError && (
        <p className="mt-4 text-xs text-[var(--pink)]">{saveError}</p>
      )}

      {isSaved ? (
        <div className="mt-6 flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-warm)] p-3">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-[var(--sky)]" />
          <p className="text-sm text-[var(--text)]">
            Saved. Your checkpoints are set.
          </p>
        </div>
      ) : (
        <button
          type="button"
          onClick={handleSaveAll}
          disabled={isSaving}
          className="mt-6 flex items-center justify-center gap-2 rounded-md bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
        >
          {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSaving ? "Saving..." : "Save All"}
        </button>
      )}
    </main>
  );
}

export default ReviewImportedProgressPage;
