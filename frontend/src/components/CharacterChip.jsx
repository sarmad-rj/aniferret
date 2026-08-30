import { User } from "lucide-react";

function CharacterChip({ character, onSelect }) {
  const handleClick = (event) => {
    event.stopPropagation();
    onSelect(character);
  };

  return (
    <li>
      <button
        type="button"
        onClick={handleClick}
        className="flex items-center gap-2 rounded-md bg-[var(--surface)] px-2 py-1.5 text-left"
      >
        {character.avatar_url ? (
          <img
            src={character.avatar_url}
            alt={character.name}
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface-warm)]">
            <User className="h-4 w-4 text-[var(--ferret)]" />
          </span>
        )}
        <span className="flex flex-col">
          <span className="text-xs font-medium text-[var(--text)]">
            {character.name}
          </span>
          {character.role && (
            <span className="text-[10px] text-[var(--text-muted)]">
              {character.role}
            </span>
          )}
        </span>
      </button>
    </li>
  );
}

export default CharacterChip;
