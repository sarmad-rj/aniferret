import { Eye } from "lucide-react";
import { formatCheckpointLabel } from "../lib/checkpoint";

function collectForeshadowedFacts(dossier) {
  const allFacts = [
    ...dossier.characters.flatMap((character) => character.revealed_facts),
    ...dossier.factions.flatMap((faction) => faction.revealed_facts),
  ];

  const factsById = new Map();
  allFacts
    .filter((fact) => fact.first_hinted_at)
    .forEach((fact) => factsById.set(fact.fact_id, fact));

  return [...factsById.values()];
}

function ForeshadowingIndex({ dossier }) {
  const facts = collectForeshadowedFacts(dossier);

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold text-[var(--primary)]">
        Foreshadowing Index
      </h2>

      {facts.length === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">
          No foreshadowed reveals are unlocked yet at this checkpoint.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {facts.map((fact) => (
            <article
              key={fact.fact_id}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
            >
              <p className="mb-2 text-sm font-semibold text-[var(--text)]">
                {fact.subject} — {fact.predicate.replaceAll("_", " ")}
              </p>
              <div className="flex flex-col gap-1.5 text-xs sm:flex-row sm:items-center sm:gap-3">
                <span className="inline-flex items-center gap-1 rounded-full bg-[var(--sky)] px-2.5 py-1 font-medium text-[var(--primary)]">
                  <Eye className="h-3 w-3" />
                  Setup: {formatCheckpointLabel(fact.first_hinted_at)}
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-[var(--pink-light)] px-2.5 py-1 font-medium text-[var(--primary)]">
                  Payoff: {fact.source_citation}
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default ForeshadowingIndex;
