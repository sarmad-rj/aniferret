import FactionCard from "./FactionCard";

function FactionHierarchy({ factions, characters }) {
  if (factions.length === 0) {
    return null;
  }

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold text-[var(--primary)]">
        Faction Hierarchy
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {factions.map((faction) => (
          <FactionCard
            key={faction.id}
            faction={faction}
            members={characters.filter(
              (character) => character.faction_id === faction.id,
            )}
          />
        ))}
      </div>
    </section>
  );
}

export default FactionHierarchy;
