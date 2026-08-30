import { useState } from "react";
import CharacterDossierModal from "./CharacterDossierModal";
import FactionHierarchy from "./FactionHierarchy";
import FactionMembersModal from "./FactionMembersModal";
import ForeshadowingIndex from "./ForeshadowingIndex";

function DossierView({ dossier, isRewatchMode }) {
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [selectedFactionGroup, setSelectedFactionGroup] = useState(null);

  if (!dossier) {
    return null;
  }

  if (isRewatchMode) {
    return <ForeshadowingIndex dossier={dossier} />;
  }

  const selectedCharacterFaction = dossier.factions.find(
    (faction) => faction.id === selectedCharacter?.faction_id,
  );

  const handleSelectCharacter = (character) => {
    setSelectedFactionGroup(null);
    setSelectedCharacter(character);
  };

  return (
    <div className="flex flex-col gap-6">
      <FactionHierarchy
        factions={dossier.factions}
        characters={dossier.characters}
        onSelectCharacter={handleSelectCharacter}
        onSelectFactionGroup={setSelectedFactionGroup}
      />

      {selectedFactionGroup && (
        <FactionMembersModal
          faction={selectedFactionGroup.faction}
          members={selectedFactionGroup.members}
          onSelectCharacter={handleSelectCharacter}
          onClose={() => setSelectedFactionGroup(null)}
        />
      )}

      {selectedCharacter && (
        <CharacterDossierModal
          character={selectedCharacter}
          factionName={selectedCharacterFaction?.name}
          onClose={() => setSelectedCharacter(null)}
        />
      )}
    </div>
  );
}

export default DossierView;
