import FactionTreeNode from "./FactionTreeNode";

const UNAFFILIATED_NODE_META = {
  id: "unaffiliated",
  name: "Unaffiliated",
  description: "Introduced characters not yet tied to a known faction.",
  children: [],
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
      .map((crew) => ({
        id: crew.id,
        name: crew.name,
        description: crew.description,
        members: membersOf(crew.id),
        children: [],
      }));

  const unaffiliatedMembers = characters.filter(
    (character) => !character.faction_id,
  );

  if (topLevelFactions.length === 0 && unaffiliatedMembers.length === 0) {
    return null;
  }

  const treeNodes = topLevelFactions.map((faction) => ({
    id: faction.id,
    name: faction.name,
    description: faction.description,
    members: membersOf(faction.id),
    children: crewsOf(faction.id),
  }));

  if (unaffiliatedMembers.length > 0) {
    treeNodes.push({ ...UNAFFILIATED_NODE_META, members: unaffiliatedMembers });
  }

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold text-[var(--primary)]">
        Faction Hierarchy
      </h2>
      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-warm)] px-4">
        {treeNodes.map((node) => (
          <div
            key={node.id}
            className="border-b border-[var(--border)] last:border-b-0"
          >
            <FactionTreeNode
              node={node}
              depth={0}
              defaultOpen
              onSelectCharacter={onSelectCharacter}
              onSelectFactionGroup={onSelectFactionGroup}
            />
          </div>
        ))}
      </div>
    </section>
  );
}

export default FactionHierarchy;
