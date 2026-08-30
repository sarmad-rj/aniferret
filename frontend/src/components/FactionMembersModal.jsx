import { X } from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";
import CharacterGrid from "./CharacterGrid";

function FactionMembersModal({ faction, members, onSelectCharacter, onClose }) {
  useBodyScrollLock();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-y-auto rounded-lg bg-[var(--surface)] p-5"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[var(--primary)]">
              {faction.name}
            </h2>
            {faction.description && (
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {faction.description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close faction members"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        {members.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">
            No known members introduced yet at this checkpoint.
          </p>
        ) : (
          <CharacterGrid
            characters={members}
            onSelectCharacter={onSelectCharacter}
            title={null}
          />
        )}
      </div>
    </div>
  );
}

export default FactionMembersModal;
