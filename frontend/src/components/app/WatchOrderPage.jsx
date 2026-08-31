import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import useWatchOrder from "../../hooks/useWatchOrder";

const ENTRY_TYPE_LABELS = {
  tv: "TV",
  movie: "Movie",
  ova: "OVA",
};

const SORT_OPTIONS = [
  { key: "release_order", label: "Release Order" },
  { key: "chronological_order", label: "Chronological Order" },
];

function WatchOrderPage() {
  const { selectedSlug } = useOutletContext();
  const [sortKey, setSortKey] = useState("release_order");

  const { watchOrder, isLoading, error } = useWatchOrder(selectedSlug);

  const sortedEntries = watchOrder
    ? [...watchOrder.entries].sort((a, b) => a[sortKey] - b[sortKey])
    : [];

  return (
    <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <h1 className="mb-1 text-xl font-bold text-[var(--primary)]">
        Watch Order{watchOrder ? `: ${watchOrder.franchise_name}` : ""}
      </h1>
      <p className="mb-6 text-sm text-[var(--text-muted)]">
        Release order is how the world watched it. Chronological order is how
        the story actually unfolds — the two don&apos;t always agree.
      </p>

      {!selectedSlug && (
        <p className="text-sm text-[var(--text-muted)]">
          Select an anime to see its watch order.
        </p>
      )}

      {error && (
        <p className="text-sm text-[var(--text-muted)]">
          No watch order guide is available for this anime yet.
        </p>
      )}

      {selectedSlug && !error && isLoading && (
        <p className="text-sm text-[var(--text-muted)]">
          Loading watch order...
        </p>
      )}

      {watchOrder && (
        <>
          <div className="mb-6 inline-flex rounded-md border border-[var(--border)] bg-[var(--surface)] p-1">
            {SORT_OPTIONS.map((option) => (
              <button
                key={option.key}
                type="button"
                onClick={() => setSortKey(option.key)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium ${
                  sortKey === option.key
                    ? "bg-[var(--primary)] text-[var(--surface)]"
                    : "text-[var(--text-muted)]"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>

          <ol className="flex flex-col gap-3">
            {sortedEntries.map((entry, index) => (
              <li
                key={entry.id}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--surface-warm)] text-xs font-bold text-[var(--primary)]">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold text-[var(--text)]">
                        {entry.title}
                      </h3>
                      <span className="rounded-full bg-[var(--sky)]/25 px-2.5 py-0.5 text-xs font-medium text-[var(--primary)]">
                        {ENTRY_TYPE_LABELS[entry.entry_type] ??
                          entry.entry_type}
                      </span>
                    </div>
                    {entry.note && (
                      <p className="mb-2 text-xs text-[var(--text-muted)]">
                        {entry.note}
                      </p>
                    )}
                    {entry.anime_slug && (
                      <Link
                        to={`/app/dossiers?anime=${entry.anime_slug}`}
                        className="text-xs font-medium text-[var(--ferret)]"
                      >
                        View Dossier &rarr;
                      </Link>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </main>
  );
}

export default WatchOrderPage;
