import { useState } from "react";
import { Lock, User, X } from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";

function StatField({ label, value }) {
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

function splitIntoParagraphs(text) {
  const normalized = text.replace(/\r\n/g, "\n");
  const doubleBreakParagraphs = normalized
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  if (doubleBreakParagraphs.length > 1) {
    return doubleBreakParagraphs;
  }

  return normalized
    .split("\n")
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
}

function BackstorySection({ backstory }) {
  if (!backstory) {
    return null;
  }

  const paragraphs = splitIntoParagraphs(backstory);

  return (
    <div className="rounded-md bg-[var(--surface-warm)] px-3 py-2.5">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Backstory
      </span>
      <div className="mt-1.5 flex flex-col gap-2">
        {paragraphs.map((paragraph, index) => (
          // eslint-disable-next-line react/no-array-index-key
          <p key={index} className="text-sm leading-relaxed text-[var(--text)]">
            {paragraph}
          </p>
        ))}
      </div>
    </div>
  );
}

function AvatarLightbox({ imageUrl, name, onClose }) {
  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-[var(--primary)]/70 p-6"
      onClick={(event) => {
        event.stopPropagation();
        onClose();
      }}
    >
      <div className="relative flex max-h-full max-w-full flex-col items-center">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onClose();
          }}
          aria-label="Close image"
          className="absolute -top-3 -right-3 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface)] shadow-md"
        >
          <X className="h-4 w-4 text-[var(--primary)]" />
        </button>
        <img
          src={imageUrl}
          alt={name}
          className="max-h-[80vh] max-w-full rounded-lg object-contain"
          onClick={(event) => event.stopPropagation()}
        />
      </div>
    </div>
  );
}

function CharacterDossierModal({ character, factionName, onClose }) {
  const [isImageOpen, setIsImageOpen] = useState(false);

  useBodyScrollLock();

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
              <button
                type="button"
                onClick={() => setIsImageOpen(true)}
                aria-label={`View ${character.name}'s image`}
                className="shrink-0"
              >
                <img
                  src={character.avatar_url}
                  alt={character.name}
                  className="h-16 w-16 cursor-pointer rounded-full border border-[var(--border)] object-cover transition-opacity hover:opacity-80"
                />
              </button>
            ) : (
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-[var(--surface-warm)]">
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

        <div className="flex flex-col gap-2">
          <StatField label="Power / Ability" value={character.power} />
          <StatField label="Bounty" value={character.bounty} />
          <BackstorySection backstory={character.backstory} />
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

      {isImageOpen && character.avatar_url && (
        <AvatarLightbox
          imageUrl={character.avatar_url}
          name={character.name}
          onClose={() => setIsImageOpen(false)}
        />
      )}
    </div>
  );
}

export default CharacterDossierModal;
