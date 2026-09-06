import useAnimeCatalog from "../../hooks/useAnimeCatalog";
import AnimeCoverCard from "../AnimeCoverCard";

function DiscoverPage() {
  const { animeList, isLoading, error } = useAnimeCatalog();

  return (
    <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <h1 className="mb-1 text-xl font-bold text-[var(--primary)]">Discover</h1>
      <p className="mb-6 text-sm text-[var(--text-muted)]">
        Browse the spoiler-audited collection and pick a show to explore.
      </p>

      {error && (
        <p className="text-sm text-[var(--text-muted)]">
          Could not reach the AniFerret backend. Is it running?
        </p>
      )}

      {!error && isLoading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {["one", "two", "three", "four", "five", "six"].map(
            (placeholderKey) => (
              <div
                key={placeholderKey}
                className="h-80 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]"
              />
            ),
          )}
        </div>
      )}

      {!error && !isLoading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {animeList.map((anime) => (
            <AnimeCoverCard
              key={anime.slug}
              anime={anime}
              linkTo={`/app/dossiers?anime=${anime.slug}`}
            />
          ))}
        </div>
      )}
    </main>
  );
}

export default DiscoverPage;
