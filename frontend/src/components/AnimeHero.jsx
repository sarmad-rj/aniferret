import { Film } from "lucide-react";
import { parseCheckpointEpisode } from "../lib/checkpoint";

function AnimeHero({ anime, checkpoint }) {
  if (!anime) {
    return null;
  }

  const episode = parseCheckpointEpisode(checkpoint);

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 sm:flex-row sm:p-6">
      {anime.cover_image_url ? (
        <img
          src={anime.cover_image_url}
          alt={anime.title}
          className="h-56 w-40 shrink-0 self-center rounded-md object-cover shadow-sm sm:self-start"
        />
      ) : (
        <div className="flex h-56 w-40 shrink-0 items-center justify-center self-center rounded-md bg-[var(--surface-warm)] sm:self-start">
          <Film className="h-8 w-8 text-[var(--ferret)]" />
        </div>
      )}

      <div className="flex flex-1 flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h1 className="text-2xl font-semibold text-[var(--primary)] sm:text-3xl">
            {anime.title}
          </h1>
          {anime.score != null && (
            <div className="flex shrink-0 flex-col items-center rounded-md border border-[var(--border)] bg-[var(--surface-warm)] px-4 py-2 text-center">
              <span className="text-xl font-bold text-[var(--ferret)]">
                {anime.score.toFixed(2)}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                MAL Score
              </span>
            </div>
          )}
        </div>

        {anime.genres?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {anime.genres.map((genre) => (
              <span
                key={genre}
                className="rounded-full bg-[var(--sky)]/25 px-2.5 py-1 text-xs font-medium text-[var(--primary)]"
              >
                {genre}
              </span>
            ))}
          </div>
        )}

        {anime.synopsis && (
          <p className="text-sm leading-relaxed text-[var(--text-muted)]">
            {anime.synopsis}
          </p>
        )}

        {episode !== null && (
          <span className="inline-flex w-fit items-center gap-1 rounded-full bg-[var(--sky)]/30 px-3 py-1 text-xs font-medium text-[var(--primary)]">
            Currently on Episode {episode}
          </span>
        )}
      </div>
    </section>
  );
}

export default AnimeHero;
