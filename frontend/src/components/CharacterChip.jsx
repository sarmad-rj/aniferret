import { User } from "lucide-react";

function CharacterChip({ character, onSelect }) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(character)}
        className="inline-flex items-center gap-1.5 rounded-full bg-[var(--surface)] py-1 pl-1 pr-2.5 text-xs text-[var(--text)]"
      >
        {character.avatar_url ? (
          <img
            src={character.avatar_url}
            alt={character.name}
            className="h-5 w-5 rounded-full object-cover"
          />
        ) : (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--surface-warm)]">
            <User className="h-3 w-3 text-[var(--ferret)]" />
          </span>
        )}
        {character.name}
      </button>
    </li>
  );
}

export default CharacterChip;
