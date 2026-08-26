import { Lock, User } from "lucide-react";

function CharacterCard({ character }) {
  return (
    <article className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="mb-2 flex items-center gap-2">
        <User className="h-4 w-4 text-[var(--primary)]" />
        <h3 className="text-sm font-semibold text-[var(--text)]">
          {character.name}
        </h3>
      </div>

      {character.revealed_facts.length === 0 ? (
        <p className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
          <Lock className="h-3 w-3 text-[var(--pink)]" />
          No lore revealed yet
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {character.revealed_facts.map((fact) => (
            <li
              key={fact.fact_id}
              className="rounded-md bg-[var(--surface-warm)] px-2 py-1.5 text-xs text-[var(--text)]"
            >
              <span className="font-medium">
                {fact.predicate.replaceAll("_", " ")}:
              </span>{" "}
              {fact.object}
              <div className="mt-0.5 text-[var(--text-muted)]">
                {fact.source_citation}
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default CharacterCard;
