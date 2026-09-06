import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, Settings, Trash2 } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useAdminAnime from "../../hooks/useAdminAnime";
import { bulkDeleteAdminAnime, deleteAdminAnime } from "../../lib/api";
import ImportAnimeModal from "../ImportAnimeModal";
import ConfirmDeleteModal from "./ConfirmDeleteModal";

function AdminAnimePage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleteError, setDeleteError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState(new Set());

  const { token } = useAuth();
  const {
    animeList,
    isLoading,
    error: fetchError,
    refetch,
  } = useAdminAnime(token);

  const trimmedQuery = searchQuery.trim().toLowerCase();
  const visibleAnimeList = trimmedQuery
    ? animeList.filter(
        (anime) =>
          anime.title.toLowerCase().includes(trimmedQuery) ||
          anime.slug.toLowerCase().includes(trimmedQuery),
      )
    : animeList;

  const visibleSelectedCount = visibleAnimeList.filter((anime) =>
    selectedIds.has(anime.id),
  ).length;
  const areAllVisibleSelected =
    visibleAnimeList.length > 0 &&
    visibleSelectedCount === visibleAnimeList.length;

  const handleImported = () => {
    setIsImportModalOpen(false);
    refetch();
  };

  const toggleSelected = (animeId) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (next.has(animeId)) {
        next.delete(animeId);
      } else {
        next.add(animeId);
      }
      return next;
    });
  };

  const toggleSelectAllVisible = () => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (areAllVisibleSelected) {
        visibleAnimeList.forEach((anime) => next.delete(anime.id));
      } else {
        visibleAnimeList.forEach((anime) => next.add(anime.id));
      }
      return next;
    });
  };

  const handleConfirmDelete = async () => {
    // Deliberately doesn't catch here: a total failure (network/500) should
    // propagate up to ConfirmDeleteModal's own inline error and keep the modal
    // open. A partial bulk failure is different -- some items DID get deleted, so
    // that's treated as a completed action (modal closes) with a summary surfaced
    // on the page instead.
    if (pendingDelete.type === "single") {
      await deleteAdminAnime(token, pendingDelete.anime.id);
      await refetch();
      setPendingDelete(null);
      setDeleteError(null);
    } else {
      const result = await bulkDeleteAdminAnime(token, pendingDelete.ids);
      await refetch();
      setSelectedIds(new Set());
      setPendingDelete(null);
      setDeleteError(
        result.failed.length > 0
          ? `${result.deleted_ids.length} deleted, ${result.failed.length} could not be deleted.`
          : null,
      );
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-[var(--primary)]">
          Anime Management
        </h1>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <button
              type="button"
              onClick={() =>
                setPendingDelete({ type: "bulk", ids: Array.from(selectedIds) })
              }
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--pink)] px-3 py-1.5 text-sm font-medium text-[var(--pink)]"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete Selected ({selectedIds.size})
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsImportModalOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--primary)] px-3 py-1.5 text-sm font-medium text-[var(--surface)]"
          >
            <Plus className="h-3.5 w-3.5" />
            Import Anime
          </button>
        </div>
      </div>

      {(fetchError || deleteError) && (
        <p className="mb-4 rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          {deleteError ?? "Could not load anime."}
        </p>
      )}

      {!isLoading && animeList.length > 0 && (
        <div className="relative mb-4 max-w-xs">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search by title or slug..."
            aria-label="Search anime"
            className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-1.5 pl-8 pr-3 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)]"
          />
        </div>
      )}

      {isLoading ? (
        <div className="h-40 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                <th className="w-8 px-4 py-3">
                  {visibleAnimeList.length > 0 && (
                    <input
                      type="checkbox"
                      checked={areAllVisibleSelected}
                      onChange={toggleSelectAllVisible}
                      aria-label="Select all anime"
                    />
                  )}
                </th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Episodes</th>
                <th className="px-4 py-3">Characters</th>
                <th className="px-4 py-3">Facts</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {visibleAnimeList.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-6 text-center text-[var(--text-muted)]"
                  >
                    {animeList.length === 0
                      ? "No anime tracked yet."
                      : "No anime matches your search."}
                  </td>
                </tr>
              ) : (
                visibleAnimeList.map((anime) => (
                  <tr
                    key={anime.id}
                    className="border-b border-[var(--border)] last:border-0"
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(anime.id)}
                        onChange={() => toggleSelected(anime.id)}
                        aria-label={`Select ${anime.title}`}
                      />
                    </td>
                    <td className="px-4 py-3 font-medium text-[var(--text)]">
                      <Link
                        to={`/admin/anime/${anime.id}`}
                        className="hover:underline"
                      >
                        {anime.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {anime.slug}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {anime.total_episodes}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {anime.character_count}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {anime.fact_count}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-3">
                        <Link
                          to={`/admin/anime/${anime.id}`}
                          aria-label={`Manage ${anime.title}`}
                          className="text-[var(--primary)]"
                        >
                          <Settings className="h-4 w-4" />
                        </Link>
                        <button
                          type="button"
                          onClick={() =>
                            setPendingDelete({ type: "single", anime })
                          }
                          aria-label={`Delete ${anime.title}`}
                          className="text-[var(--pink)]"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {isImportModalOpen && (
        <ImportAnimeModal
          token={token}
          onImported={handleImported}
          onClose={() => setIsImportModalOpen(false)}
        />
      )}

      {pendingDelete?.type === "single" && (
        <ConfirmDeleteModal
          title="Delete Anime"
          description={`Delete "${pendingDelete.anime.title}"? This removes its characters, factions, facts, and any user watch progress for it.`}
          onConfirm={handleConfirmDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
      {pendingDelete?.type === "bulk" && (
        <ConfirmDeleteModal
          title="Delete Selected Anime"
          description={`Delete ${pendingDelete.ids.length} anime? This removes their characters, factions, facts, and any user watch progress for them.`}
          onConfirm={handleConfirmDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
    </main>
  );
}

export default AdminAnimePage;
