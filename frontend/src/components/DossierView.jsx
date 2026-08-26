import CharacterGrid from "./CharacterGrid";
import FactionHierarchy from "./FactionHierarchy";
import ForeshadowingIndex from "./ForeshadowingIndex";

function DossierView({ dossier, isRewatchMode }) {
  if (!dossier) {
    return null;
  }

  if (isRewatchMode) {
    return <ForeshadowingIndex dossier={dossier} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <FactionHierarchy
        factions={dossier.factions}
        characters={dossier.characters}
      />
      <CharacterGrid characters={dossier.characters} />
    </div>
  );
}

export default DossierView;
