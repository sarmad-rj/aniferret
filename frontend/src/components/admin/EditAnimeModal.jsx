import { useState } from "react";
import { Pencil, X } from "lucide-react";
import useBodyScrollLock from "../../hooks/useBodyScrollLock";
import { updateAdminAnimeMetadata } from "../../lib/api";

function parseGenres(text) {
  return text
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

function EditAnimeModal({ anime, token, onSaved, onClose }) {
  const [title, setTitle] = useState(anime.title);
  const [coverImageUrl, setCoverImageUrl] = useState(
    anime.cover_image_url ?? "",
  );
  const [genresText, setGenresText] = useState((anime.genres ?? []).join(", "));
  const [synopsis, setSynopsis] = useState(anime.synopsis ?? "");
  const [score, setScore] = useState(
    anime.score != null ? String(anime.score) : "",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useBodyScrollLock();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting || !title.trim()) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await updateAdminAnimeMetadata(token, anime.id, {
        title: title.trim(),
        cover_image_url: coverImageUrl.trim() || null,
        genres: parseGenres(genresText),
        synopsis: synopsis.trim() || null,
        score: score.trim() ? Number(score) : null,
      });
      onSaved();
    } catch (submitError) {
      setError(
        submitError.status === 422
          ? "Score must be between 0 and 10."
          : "Could not save those changes. Please try again.",
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
            <Pencil className="h-4 w-4 text-[var(--ferret)]" />
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Edit Anime
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close edit anime"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto"
        >
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Title
            <input
              type="text"
              required
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Cover Image URL
            <input
              type="text"
              value={coverImageUrl}
              onChange={(event) => setCoverImageUrl(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Genres (comma-separated)
            <input
              type="text"
              value={genresText}
              onChange={(event) => setGenresText(event.target.value)}
              placeholder="Action, Drama"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Synopsis
            <textarea
              value={synopsis}
              onChange={(event) => setSynopsis(event.target.value)}
              rows={3}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
            Score (0-10)
            <input
              type="number"
              min={0}
              max={10}
              step={0.01}
              value={score}
              onChange={(event) => setScore(event.target.value)}
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          </label>

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting || !title.trim()}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default EditAnimeModal;
