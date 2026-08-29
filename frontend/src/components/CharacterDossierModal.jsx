import { Lock, User, X } from "lucide-react";
import { formatCheckpointLabel } from "../lib/checkpoint";

function SpoilerField({ label, value, isRevealed }) {
  if (!isRevealed) {
    return (
      <div className="rounded-md bg-[var(--pink-light)] px-3 py-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--primary)]">
          {label}
        </span>
        <p className="mt-0.5 flex items-center gap-1 text-xs text-[var(--primary)]">
          <Lock className="h-3 w-3 text-[var(--pink)]" />
          Locked
        </p>
      </div>
    );
  }

  if (!value) {
    return null;
  }

  return (
    <div className="rounded-md bg-[var(--surface-warm)] px-3 py-2">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        {label}
      </span>
      <p className="mt-0.5 text-sm text-[var(--text)]">{value}</p>
    </div>
  );
}

function CharacterDossierModal({ character, factionName, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-lg flex-col overflow-y-auto rounded-lg bg-[var(--surface)] p-5"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {character.avatar_url ? (
              <img
                src={character.avatar_url}
                alt={character.name}
                className="h-16 w-16 rounded-full border border-[var(--border)] object-cover"
              />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--surface-warm)]">
                <User className="h-7 w-7 text-[var(--ferret)]" />
              </div>
            )}
            <div>
              <h2 className="text-base font-semibold text-[var(--primary)]">
                {character.name}
              </h2>
              <div className="mt-1 flex flex-wrap gap-1.5 text-xs text-[var(--text-muted)]">
                {character.role && <span>{character.role}</span>}
                {character.role && character.height && <span>&middot;</span>}
                {character.height && <span>{character.height}</span>}
                {factionName && <span>&middot; {factionName}</span>}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close character dossier"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        {!character.is_revealed && (
          <p className="mb-3 inline-flex w-fit items-center gap-1 rounded-full bg-[var(--pink-light)] px-3 py-1 text-xs font-medium text-[var(--primary)]">
            <Lock className="h-3.5 w-3.5 text-[var(--pink)]" />
            Full dossier unlocks at{" "}
            {formatCheckpointLabel(character.first_revealed_at)}
          </p>
        )}

        <div className="flex flex-col gap-2">
          <SpoilerField
            label="Devil Fruit / Power"
            value={character.power}
            isRevealed={character.is_revealed}
          />
          <SpoilerField
            label="Bounty"
            value={character.bounty}
            isRevealed={character.is_revealed}
          />
          <SpoilerField
            label="Backstory"
            value={character.backstory}
            isRevealed={character.is_revealed}
          />
        </div>

        <div className="mt-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Unlocked Temporal Facts
          </h3>
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
        </div>
      </div>
    </div>
  );
}

export default CharacterDossierModal;
