import { useEffect, useRef, useState } from "react";
import { Outlet, useSearchParams } from "react-router-dom";
import Header from "../Header";
import NavBar from "../NavBar";
import GroupModeModal from "../GroupModeModal";
import GroupModeBanner from "../GroupModeBanner";
import ImportAnimeModal from "../ImportAnimeModal";
import useAnimeCatalog from "../../hooks/useAnimeCatalog";
import { buildCheckpointSequence } from "../../lib/checkpoint";

function AppLayout() {
  const [searchParams] = useSearchParams();
  const [selectedSlug, setSelectedSlug] = useState(null);
  const [checkpoint, setCheckpoint] = useState(null);
  const [isRewatchMode, setIsRewatchMode] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [groupCheckpoint, setGroupCheckpoint] = useState(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const selectedSlugRef = useRef(selectedSlug);

  const {
    animeList,
    error: animeError,
    refetch: refetchAnimeList,
  } = useAnimeCatalog();

  const selectedAnime =
    animeList.find((anime) => anime.slug === selectedSlug) ?? null;
  const isGroupModeActive = groupCheckpoint !== null;
  const activeCheckpoint = isGroupModeActive ? groupCheckpoint : checkpoint;

  useEffect(() => {
    selectedSlugRef.current = selectedSlug;
  }, [selectedSlug]);

  useEffect(() => {
    if (animeList.length === 0) {
      return;
    }
    const requestedSlug = searchParams.get("anime");
    const requestedAnime = animeList.find(
      (anime) => anime.slug === requestedSlug,
    );

    if (requestedAnime && requestedAnime.slug !== selectedSlugRef.current) {
      setSelectedSlug(requestedAnime.slug);
      setCheckpoint(null);
      setGroupCheckpoint(null);
      return;
    }

    if (!selectedSlugRef.current) {
      setSelectedSlug(animeList[0].slug);
    }
    // Reads selectedSlugRef instead of depending on selectedSlug: this effect should
    // only re-sync from the URL when the URL itself changes (a Discover/Watch-Order
    // link navigation), not when selectedSlug changes via the header dropdown —
    // otherwise a stale ?anime= param fights every manual selection back to itself.
  }, [animeList, searchParams]);

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

  const handleAnimeImported = async (importedAnime) => {
    setIsImportModalOpen(false);
    await refetchAnimeList();
    handleSelectAnime(importedAnime.slug);
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
        onOpenImport={() => setIsImportModalOpen(true)}
      />
      <NavBar />

      {animeError && (
        <p className="mx-auto mt-6 max-w-6xl rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          Could not reach the AniFerret backend. Is it running?
        </p>
      )}

      {isGroupModeActive && (
        <div className="mx-auto mt-6 max-w-6xl px-4 sm:px-6">
          <GroupModeBanner
            checkpoint={groupCheckpoint}
            onExit={handleExitGroupMode}
          />
        </div>
      )}

      <Outlet
        context={{
          animeList,
          selectedAnime,
          selectedSlug,
          activeCheckpoint,
          isGroupModeActive,
          setCheckpoint,
          isRewatchMode,
          setIsRewatchMode,
          onOpenGroupModal: () => setIsGroupModalOpen(true),
        }}
      />

      {isGroupModalOpen && checkpointSequence.length > 0 && (
        <GroupModeModal
          checkpointSequence={checkpointSequence}
          onApply={handleApplyGroupMode}
          onClose={() => setIsGroupModalOpen(false)}
        />
      )}

      {isImportModalOpen && (
        <ImportAnimeModal
          onImported={handleAnimeImported}
          onClose={() => setIsImportModalOpen(false)}
        />
      )}
    </div>
  );
}

export default AppLayout;
