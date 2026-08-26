import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import Header from "./components/Header";
import NavBar from "./components/NavBar";
import ProgressSlider from "./components/ProgressSlider";
import RewatchModeToggle from "./components/RewatchModeToggle";
import GroupModeModal from "./components/GroupModeModal";
import GroupModeBanner from "./components/GroupModeBanner";
import DossierView from "./components/DossierView";
import SourceConflicts from "./components/SourceConflicts";
import LoreAssistant from "./components/LoreAssistant";
import useAnimeCatalog from "./hooks/useAnimeCatalog";
import useDossier from "./hooks/useDossier";
import { buildCheckpointSequence } from "./lib/checkpoint";

function App() {
  const [selectedSlug, setSelectedSlug] = useState(null);
  const [checkpoint, setCheckpoint] = useState(null);
  const [isRewatchMode, setIsRewatchMode] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [groupCheckpoint, setGroupCheckpoint] = useState(null);

  const { animeList, error: animeError } = useAnimeCatalog();

  const selectedAnime =
    animeList.find((anime) => anime.slug === selectedSlug) ?? null;
  const isGroupModeActive = groupCheckpoint !== null;
  const activeCheckpoint = isGroupModeActive ? groupCheckpoint : checkpoint;

  const {
    dossier,
    isLoading: isDossierLoading,
    error: dossierError,
  } = useDossier(selectedSlug, activeCheckpoint);

  useEffect(() => {
    if (!selectedSlug && animeList.length > 0) {
      setSelectedSlug(animeList[0].slug);
    }
  }, [animeList, selectedSlug]);

  useEffect(() => {
    if (selectedAnime && !checkpoint) {
      const sequence = buildCheckpointSequence(
        selectedAnime.season_episode_counts,
      );
      setCheckpoint(sequence[0] ?? null);
    }
  }, [selectedAnime, checkpoint]);

  const handleSelectAnime = (slug) => {
    setSelectedSlug(slug);
    setCheckpoint(null);
    setGroupCheckpoint(null);
  };

  const handleApplyGroupMode = (effectiveCheckpoint) => {
    setGroupCheckpoint(effectiveCheckpoint);
    setIsGroupModalOpen(false);
  };

  const handleExitGroupMode = () => {
    setGroupCheckpoint(null);
  };

  const checkpointSequence = selectedAnime
    ? buildCheckpointSequence(selectedAnime.season_episode_counts)
    : [];

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <Header
        animeList={animeList}
        selectedSlug={selectedSlug}
        onSelectAnime={handleSelectAnime}
      />
      <NavBar />

      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6">
        {animeError && (
          <p className="rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
            Could not reach the AniFerret backend. Is it running?
          </p>
        )}

        {isGroupModeActive && (
          <GroupModeBanner
            checkpoint={groupCheckpoint}
            onExit={handleExitGroupMode}
          />
        )}

        {selectedAnime && (
          <ProgressSlider
            anime={selectedAnime}
            checkpoint={activeCheckpoint}
            onCheckpointChange={setCheckpoint}
            disabled={isGroupModeActive}
          />
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-lg font-semibold text-[var(--primary)]">
            {selectedAnime ? selectedAnime.title : "Loading..."}
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setIsGroupModalOpen(true)}
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
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="flex flex-col gap-6 lg:col-span-2">
            {isDossierLoading && (
              <p className="text-sm text-[var(--text-muted)]">
                Loading dossier...
              </p>
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
          </div>

          <div className="lg:col-span-1">
            {selectedSlug && activeCheckpoint && (
              <LoreAssistant
                animeSlug={selectedSlug}
                checkpoint={activeCheckpoint}
              />
            )}
          </div>
        </div>
      </main>

      {isGroupModalOpen && checkpointSequence.length > 0 && (
        <GroupModeModal
          checkpointSequence={checkpointSequence}
          onApply={handleApplyGroupMode}
          onClose={() => setIsGroupModalOpen(false)}
        />
      )}
    </div>
  );
}

export default App;
