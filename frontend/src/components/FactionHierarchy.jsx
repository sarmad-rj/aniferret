import FactionCard from "./FactionCard";

const UNAFFILIATED_FACTION = {
  id: "unaffiliated",
  name: "Unaffiliated",
  description: "Introduced characters not yet tied to a known faction.",
  parent_id: null,
};

function FactionHierarchy({
  factions,
  characters,
  onSelectCharacter,
  onSelectFactionGroup,
}) {
  const membersOf = (factionId) =>
    characters.filter((character) => character.faction_id === factionId);

  const topLevelFactions = factions.filter((faction) => !faction.parent_id);
  const crewsOf = (parentId) =>
    factions
      .filter((faction) => faction.parent_id === parentId)
      .map((crew) => ({ faction: crew, members: membersOf(crew.id) }));

  const unaffiliatedMembers = characters.filter(
    (character) => !character.faction_id,
  );

  if (topLevelFactions.length === 0 && unaffiliatedMembers.length === 0) {
    return null;
  }

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold text-[var(--primary)]">
        Faction Hierarchy
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {topLevelFactions.map((faction) => (
          <FactionCard
            key={faction.id}
            faction={faction}
            members={membersOf(faction.id)}
            crews={crewsOf(faction.id)}
            onSelectCharacter={onSelectCharacter}
            onSelectFactionGroup={onSelectFactionGroup}
          />
        ))}
        {unaffiliatedMembers.length > 0 && (
          <FactionCard
            key={UNAFFILIATED_FACTION.id}
            faction={UNAFFILIATED_FACTION}
            members={unaffiliatedMembers}
            crews={[]}
            onSelectCharacter={onSelectCharacter}
            onSelectFactionGroup={onSelectFactionGroup}
          />
        )}
      </div>
    </section>
  );
}

export default FactionHierarchy;
