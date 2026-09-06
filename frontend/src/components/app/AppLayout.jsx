import { useEffect, useRef, useState } from "react";
import {
  Outlet,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import Header from "../Header";
import NavBar from "../NavBar";
import GroupModeModal from "../GroupModeModal";
import GroupModeBanner from "../GroupModeBanner";
import AuthModal from "../AuthModal";
import { useAuth } from "../../context/useAuth";
import useAnimeCatalog from "../../hooks/useAnimeCatalog";
import {
  buildCheckpointSequence,
  isValidCheckpointFormat,
} from "../../lib/checkpoint";
import { fetchWatchProgress, saveWatchProgress } from "../../lib/api";
import {
  getGuestCheckpoint,
  setGuestCheckpoint,
} from "../../lib/guestProgress";
import {
  getStoredSelectedSlug,
  setStoredSelectedSlug,
} from "../../lib/selectedAnime";

// Routes whose page component reads selectedAnime/selectedSlug off the Outlet
// context and reacts to it directly (see DossiersPage/LoreAssistantPage/
// WatchOrderPage's own useOutletContext() calls) — picking a new anime from the
// header dropdown while already on one of these just updates what's shown in
// place. Anywhere else under /app (Discover, Profile) ignores that context
// entirely, so without this the dropdown would silently do nothing.
const ANIME_CONTEXT_AWARE_PATHS = [
  "/app/dossiers",
  "/app/lore-assistant",
  "/app/watch-order",
];

function AppLayout() {
  const [searchParams] = useSearchParams();
  const [selectedSlug, setSelectedSlug] = useState(null);
  const [checkpoint, setCheckpoint] = useState(null);
  const [isRewatchMode, setIsRewatchMode] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [groupCheckpoint, setGroupCheckpoint] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [remoteProgressBySlug, setRemoteProgressBySlug] = useState({});
  const [progressLoadedForToken, setProgressLoadedForToken] =
    useState(undefined);
  const selectedSlugRef = useRef(selectedSlug);

  const { animeList, error: animeError } = useAnimeCatalog();
  const { isAuthenticated, isLoading: isAuthLoading, token } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const selectedAnime =
    animeList.find((anime) => anime.slug === selectedSlug) ?? null;
  const isGroupModeActive = groupCheckpoint !== null;
  const activeCheckpoint = isGroupModeActive ? groupCheckpoint : checkpoint;
  // Derived synchronously each render rather than a separate "isLoading" flag that
  // only flips true from inside an effect: on the very render isAuthenticated first
  // becomes true, an effect-order race could let the checkpoint-seeding effect below
  // run before a lagging loading flag had a chance to be set, seeding from an empty
  // remoteProgressBySlug and permanently missing the real saved checkpoint once it
  // arrived (the seeding effect never re-runs after checkpoint is set). Comparing
  // against the token itself has no such lag — it's wrong (not yet matching) on that
  // same render for free, with no dependency on effect execution order.
  const isRemoteProgressReady =
    !isAuthenticated || progressLoadedForToken === token;

  useEffect(() => {
    selectedSlugRef.current = selectedSlug;
    if (selectedSlug) {
      setStoredSelectedSlug(selectedSlug);
    }
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
      const storedSlug = getStoredSelectedSlug();
      const storedAnime = animeList.find((anime) => anime.slug === storedSlug);
      setSelectedSlug((storedAnime ?? animeList[0]).slug);
    }
    // Reads selectedSlugRef instead of depending on selectedSlug: this effect should
    // only re-sync from the URL when the URL itself changes (a Discover/Watch-Order
    // link navigation), not when selectedSlug changes via the header dropdown —
    // otherwise a stale ?anime= param fights every manual selection back to itself.
    //
    // The no-param branch (a bare reload/direct visit) falls back to the
    // last-selected anime persisted in localStorage rather than always
    // animeList[0] — otherwise every reload silently jumped back to whichever
    // anime happened to sort first, discarding whatever the user was viewing.
  }, [animeList, searchParams]);

  useEffect(() => {
    // Deliberately separate from the anime-slug sync effect above rather than
    // folded into it: that effect only resets checkpoint to null (letting the
    // saved-progress-seeding effect below fill it in) when the *anime* changes,
    // so an explicit ?checkpoint= param -- e.g. Profile's "Resume Timeline" button
    // -- would otherwise be silently dropped whenever it targets the
    // already-selected anime. checkpoint is intentionally left out of the
    // dependency array: this should apply the URL's checkpoint once selectedAnime
    // settles, not fight back every time the user moves the slider afterward.
    if (!selectedAnime) {
      return;
    }
    const requestedCheckpoint = searchParams.get("checkpoint");
    if (
      requestedCheckpoint &&
      isValidCheckpointFormat(requestedCheckpoint) &&
      requestedCheckpoint !== checkpoint
    ) {
      setCheckpoint(requestedCheckpoint);
      setGroupCheckpoint(null);
    }
    // oxlint-disable-next-line react-hooks/exhaustive-deps -- checkpoint read, not
    // depended on; see comment above.
  }, [selectedAnime, searchParams]);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setRemoteProgressBySlug({});
      setProgressLoadedForToken(undefined);
      return undefined;
    }

    let isMounted = true;
    fetchWatchProgress(token)
      .then((response) => {
        if (!isMounted) {
          return;
        }
        const bySlug = {};
        for (const entry of response.entries) {
          bySlug[entry.anime_slug] = entry.checkpoint;
        }
        setRemoteProgressBySlug(bySlug);
      })
      .catch(() => {
        // Non-fatal — checkpoint seeding just falls back to the sequence start.
      })
      .finally(() => {
        if (isMounted) {
          setProgressLoadedForToken(token);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (
      !selectedAnime ||
      checkpoint ||
      isAuthLoading ||
      !isRemoteProgressReady
    ) {
      return;
    }

    const savedCheckpoint = isAuthenticated
      ? remoteProgressBySlug[selectedAnime.slug]
      : getGuestCheckpoint(selectedAnime.slug);

    if (savedCheckpoint) {
      setCheckpoint(savedCheckpoint);
      return;
    }

    const sequence = buildCheckpointSequence(
      selectedAnime.season_episode_counts,
    );
    setCheckpoint(sequence[0] ?? null);
  }, [
    selectedAnime,
    checkpoint,
    isAuthLoading,
    isAuthenticated,
    isRemoteProgressReady,
    remoteProgressBySlug,
  ]);

  const handleSelectAnime = (slug) => {
    setSelectedSlug(slug);
    setCheckpoint(null);
    setGroupCheckpoint(null);

    const isOnAnimeContextAwarePage = ANIME_CONTEXT_AWARE_PATHS.some((path) =>
      location.pathname.startsWith(path),
    );
    if (!isOnAnimeContextAwarePage) {
      navigate(`/app/dossiers?anime=${slug}`);
    }
  };

  const handleCheckpointChange = (newCheckpoint) => {
    setCheckpoint(newCheckpoint);
    if (!selectedAnime) {
      return;
    }
    if (isAuthenticated && token) {
      saveWatchProgress(token, [
        { anime_slug: selectedAnime.slug, checkpoint: newCheckpoint },
      ]).catch(() => {
        // Non-fatal — the slider already moved locally; the save can be retried
        // implicitly next time the checkpoint changes.
      });
    } else {
      setGuestCheckpoint(selectedAnime.slug, newCheckpoint);
    }
  };

  const handleOpenGroupModal = () => {
    if (isAuthenticated) {
      setIsGroupModalOpen(true);
    } else {
      setIsAuthModalOpen(true);
    }
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
      {location.pathname !== "/app/profile" && <NavBar />}

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
          setCheckpoint: handleCheckpointChange,
          isRewatchMode,
          setIsRewatchMode,
          onOpenGroupModal: handleOpenGroupModal,
        }}
      />

      {isGroupModalOpen && checkpointSequence.length > 0 && (
        <GroupModeModal
          checkpointSequence={checkpointSequence}
          token={token}
          onApply={handleApplyGroupMode}
          onClose={() => setIsGroupModalOpen(false)}
        />
      )}

      {isAuthModalOpen && (
        <AuthModal
          contextMessage="An account is required to create or join a shared watch room in Group Mode."
          onAuthenticated={() => setIsGroupModalOpen(true)}
          onClose={() => setIsAuthModalOpen(false)}
        />
      )}
    </div>
  );
}

export default AppLayout;
