import FactionCard from "./FactionCard";

function FactionHierarchy({ factions, characters, onSelectCharacter }) {
  if (factions.length === 0) {
    return null;
  }

  const membersOf = (factionId) =>
    characters.filter((character) => character.faction_id === factionId);

  const topLevelFactions = factions.filter((faction) => !faction.parent_id);
  const crewsOf = (parentId) =>
    factions
      .filter((faction) => faction.parent_id === parentId)
      .map((crew) => ({ faction: crew, members: membersOf(crew.id) }));

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
          />
        ))}
      </div>
    </section>
  );
}

export default FactionHierarchy;
