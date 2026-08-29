import { useState } from "react";
import { Loader2, Search, X } from "lucide-react";
import { postImportAnime } from "../lib/api";

function ImportSkeleton() {
  return (
    <div className="flex flex-col gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-warm)] p-3">
      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--ferret)]" />
        Fetching metadata, roster, and extracting spoiler-safe facts with Gemini
        &mdash; this can take up to a minute.
      </div>
      <div className="h-3 w-3/4 animate-pulse rounded bg-[var(--border)]" />
      <div className="h-3 w-1/2 animate-pulse rounded bg-[var(--border)]" />
      <div className="h-3 w-2/3 animate-pulse rounded bg-[var(--border)]" />
    </div>
  );
}

function ImportAnimeModal({ onImported, onClose }) {
  const [query, setQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery || isSubmitting) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const anime = await postImportAnime(trimmedQuery);
      onImported(anime);
    } catch {
      setError(
        "Could not import that anime. Try a more specific title, or its MAL id.",
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
            <Search className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Import Anime
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close import anime"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <p className="mb-4 text-xs text-[var(--text-muted)]">
          Search by title, or paste a MyAnimeList id, to dynamically ingest a
          new series &mdash; its metadata, roster, and progress-gated lore
          facts.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. One Piece, or 21"
            disabled={isSubmitting}
            className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
          />

          {isSubmitting && <ImportSkeleton />}

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !query.trim()}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting ? "Importing..." : "Import"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ImportAnimeModal;
