import { Lock, User } from "lucide-react";

function CharacterCard({ character, onSelect }) {
  return (
    <article
      onClick={() => onSelect(character)}
      className="cursor-pointer rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 transition-shadow hover:shadow-md"
    >
      <div className="mb-2 flex items-center gap-2">
        {character.avatar_url ? (
          <img
            src={character.avatar_url}
            alt={character.name}
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface-warm)]">
            <User className="h-4 w-4 text-[var(--primary)]" />
          </span>
        )}
        <div>
          <h3 className="text-sm font-semibold text-[var(--text)]">
            {character.name}
          </h3>
          {character.role && (
            <p className="text-[11px] text-[var(--text-muted)]">
              {character.role}
            </p>
          )}
        </div>
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
