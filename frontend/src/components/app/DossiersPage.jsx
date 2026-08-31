import { Users } from "lucide-react";
import { useOutletContext } from "react-router-dom";
import AnimeHero from "../AnimeHero";
import ProgressSlider from "../ProgressSlider";
import RewatchModeToggle from "../RewatchModeToggle";
import DossierView from "../DossierView";
import SourceConflicts from "../SourceConflicts";
import useDossier from "../../hooks/useDossier";

function DossiersPage() {
  const {
    selectedAnime,
    selectedSlug,
    activeCheckpoint,
    isGroupModeActive,
    setCheckpoint,
    isRewatchMode,
    setIsRewatchMode,
    onOpenGroupModal,
  } = useOutletContext();

  const {
    dossier,
    isLoading: isDossierLoading,
    error: dossierError,
  } = useDossier(selectedSlug, activeCheckpoint);

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6">
      {selectedAnime && (
        <ProgressSlider
          anime={selectedAnime}
          checkpoint={activeCheckpoint}
          onCheckpointChange={setCheckpoint}
          disabled={isGroupModeActive}
        />
      )}

      <AnimeHero anime={selectedAnime} checkpoint={activeCheckpoint} />

      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          onClick={onOpenGroupModal}
          className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-xs font-medium text-[var(--primary)]"
        >
          <Users className="h-3.5 w-3.5" />
          Group Mode
        </button>
        <RewatchModeToggle
          isRewatchMode={isRewatchMode}
          onToggle={setIsRewatchMode}
        />
      </div>

      {isDossierLoading && (
        <p className="text-sm text-[var(--text-muted)]">Loading dossier...</p>
      )}
      {dossierError && (
        <p className="text-sm text-[var(--text-muted)]">
          Could not load dossier.
        </p>
      )}
      {!isDossierLoading && !dossierError && (
        <DossierView dossier={dossier} isRewatchMode={isRewatchMode} />
      )}
      {selectedSlug && <SourceConflicts animeSlug={selectedSlug} />}
    </main>
  );
}

export default DossiersPage;
