import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { fetchAnimeSources } from "../lib/api";

const SOURCE_LABELS = {
  jikan: "Jikan (MAL)",
  anilist: "AniList",
  aniferret: "AniFerret",
};

function SourceConflicts({ animeSlug }) {
  const [sources, setSources] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setSources(null);

    fetchAnimeSources(animeSlug)
      .then((data) => {
        if (isMounted) {
          setSources(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setSources(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [animeSlug]);

  if (!sources || sources.records.length === 0) {
    return null;
  }

  return (
    <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
      <h2 className="mb-2 text-sm font-semibold text-[var(--primary)]">
        Source Providers
      </h2>

      <div className="mb-3 flex flex-wrap gap-2">
        {sources.records.map((record) => (
          <span
            key={record.source}
            className="rounded-full bg-[var(--sky)] px-2.5 py-1 text-xs font-medium text-[var(--primary)]"
          >
            {SOURCE_LABELS[record.source] ?? record.source}
            {record.episodes != null ? ` · ${record.episodes} ep` : ""}
          </span>
        ))}
      </div>

      {sources.conflicts.length > 0 && (
        <ul className="flex flex-col gap-1.5">
          {sources.conflicts.map((conflict) => (
            <li
              key={conflict.field}
              className="flex items-start gap-1.5 rounded-md bg-[var(--pink-light)] px-2.5 py-1.5 text-xs text-[var(--primary)]"
            >
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--pink)]" />
              <span>
                Providers disagree on <strong>{conflict.field}</strong>:{" "}
                {Object.entries(conflict.values)
                  .map(
                    ([source, value]) =>
                      `${SOURCE_LABELS[source] ?? source} says ${value}`,
                  )
                  .join("; ")}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default SourceConflicts;
