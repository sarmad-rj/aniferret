import { useState } from "react";
import CharacterDossierModal from "./CharacterDossierModal";
import CharacterGrid from "./CharacterGrid";
import FactionHierarchy from "./FactionHierarchy";
import ForeshadowingIndex from "./ForeshadowingIndex";

function DossierView({ dossier, isRewatchMode }) {
  const [selectedCharacter, setSelectedCharacter] = useState(null);

  if (!dossier) {
    return null;
  }

  if (isRewatchMode) {
    return <ForeshadowingIndex dossier={dossier} />;
  }

  const selectedFaction = dossier.factions.find(
    (faction) => faction.id === selectedCharacter?.faction_id,
  );

  return (
    <div className="flex flex-col gap-6">
      <FactionHierarchy
        factions={dossier.factions}
        characters={dossier.characters}
        onSelectCharacter={setSelectedCharacter}
      />
      <CharacterGrid
        characters={dossier.characters}
        onSelectCharacter={setSelectedCharacter}
      />

      {selectedCharacter && (
        <CharacterDossierModal
          character={selectedCharacter}
          factionName={selectedFaction?.name}
          onClose={() => setSelectedCharacter(null)}
        />
      )}
    </div>
  );
}

export default DossierView;
