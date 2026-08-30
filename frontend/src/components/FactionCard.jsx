import { Users } from "lucide-react";
import CharacterChip from "./CharacterChip";

function FactionCard({
  faction,
  members,
  crews = [],
  onSelectCharacter,
  onSelectFactionGroup,
}) {
  const handleCrewClick = (event, crew) => {
    event.stopPropagation();
    onSelectFactionGroup(crew);
  };

  return (
    <article
      onClick={() => onSelectFactionGroup({ faction, members })}
      className="cursor-pointer rounded-lg border border-[var(--border)] bg-[var(--surface-warm)] p-4 transition-shadow hover:shadow-md"
    >
      <div className="mb-1 flex items-center gap-2">
        <Users className="h-4 w-4 text-[var(--ferret)]" />
        <h3 className="text-sm font-semibold text-[var(--text)]">
          {faction.name}
        </h3>
      </div>

      {faction.description && (
        <p className="mb-2 text-xs text-[var(--text-muted)]">
          {faction.description}
        </p>
      )}

      {members.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {members.map((member) => (
            <CharacterChip
              key={member.id}
              character={member}
              onSelect={onSelectCharacter}
            />
          ))}
        </ul>
      )}

      {members.length === 0 && crews.length === 0 && (
        <p className="text-xs text-[var(--text-muted)]">
          No known members introduced yet
        </p>
      )}

      {crews.length > 0 && (
        <div className="mt-3 flex flex-col gap-3 border-t border-[var(--border)] pt-3">
          {crews.map((crew) => (
            <div
              key={crew.faction.id}
              onClick={(event) => handleCrewClick(event, crew)}
              className="-m-1.5 cursor-pointer rounded-md p-1.5 hover:bg-[var(--surface)]"
            >
              <h4 className="mb-1.5 text-xs font-semibold text-[var(--primary)]">
                {crew.faction.name}
              </h4>
              {crew.members.length === 0 ? (
                <p className="text-xs text-[var(--text-muted)]">
                  No known members introduced yet
                </p>
              ) : (
                <ul className="flex flex-wrap gap-1.5">
                  {crew.members.map((member) => (
                    <CharacterChip
                      key={member.id}
                      character={member}
                      onSelect={onSelectCharacter}
                    />
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

export default FactionCard;
