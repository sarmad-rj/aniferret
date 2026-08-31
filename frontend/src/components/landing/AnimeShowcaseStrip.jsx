import AnimeCoverCard from "../AnimeCoverCard";

function AnimeShowcaseStrip({ animeList, isLoading, error }) {
  return (
    <section
      id="anime"
      className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6"
    >
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-2xl font-bold text-[var(--primary)] sm:text-3xl">
          Spoiler-audited, ready to explore
        </h2>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Every character, faction, and fact below has already been checked for
          premature reveals, episode by episode.
        </p>
      </div>

      {error && (
        <p className="text-center text-sm text-[var(--text-muted)]">
          Anime catalog unavailable right now — the collection is
          spoiler-audited and growing, check back shortly.
        </p>
      )}

      {!error && isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {["one", "two", "three", "four"].map((placeholderKey) => (
            <div
              key={placeholderKey}
              className="h-72 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]"
            />
          ))}
        </div>
      )}

      {!error && !isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {animeList.map((anime) => (
            <AnimeCoverCard
              key={anime.slug}
              anime={anime}
              linkTo={`/app/dossiers?anime=${anime.slug}`}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default AnimeShowcaseStrip;
